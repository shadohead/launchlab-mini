#include <M5Unified.h>
#include <Preferences.h>
#include <memory>
#include "acquisition.h"
#include "level_indicator.h"
#include "practice_store.h"
#include "practice_ui.h"
#include "power_status.h"
#include "usb_awake.h"
#include <HWCDC.h>
#include "power_diagnostics.h"
#include <sys/time.h>
#include <esp32-hal-cpu.h>
#include "shake_wake.h"
#include "wake_ui_state.h"
#include "rpm_estimator_setting.h"
#include "motion_acquisition.h"
#include "motion_store.h"
#include "motion_ui.h"
#include "launch_feedback.h"

static constexpr char VERSION[] = "0.10.11-sticks3-lowcpu";
#ifndef LAUNCHLAB_CPU_MHZ
#define LAUNCHLAB_CPU_MHZ 80
#endif
static_assert(LAUNCHLAB_CPU_MHZ==80 || LAUNCHLAB_CPU_MHZ==160 || LAUNCHLAB_CPU_MHZ==240,
  "CPU policy must retain the 80 MHz peripheral clock");
static constexpr uint8_t DISPLAY_ROTATION=0; // Native portrait, USB-C / Grove end down.
static constexpr uint32_t ANALOG_SAMPLE_HZ = StickS3Acquisition::SAMPLE_HZ;
#include "raw_transfer.h"
static StickS3Acquisition acquisition;
static Preferences prefs;
static StickS3Level level;
static M5Canvas screen(&M5.Display);
static PracticeHistory practice,demoPractice;
static PracticeStore practiceStore;
static PracticeUI::View historyView=PracticeUI::View::Recent;
static bool historyPage=false,demo=false,saveError=false;
static bool tournamentMode=false;
enum class TournamentView:uint8_t { RecordingOnly, Rpm };
static TournamentView tournamentView=TournamentView::RecordingOnly;

static unsigned historyOffset=0;
static uint32_t lastSaveTry=0,saveCount=0,saveErrors=0,maxSaveUs=0,newSessionAt=0;
static constexpr uint32_t HISTORY_COALESCE_MS=2000;
static constexpr uint32_t HISTORY_MAX_PENDING_MS=10000;
static constexpr uint32_t HISTORY_SAVE_RETRY_MS=5000;
static uint32_t lastAcceptedAt=0,historyPendingSince=0;
static bool screenReady=false;
static bool diagnostics=false,extPower=false,stress=false,dirty=true;
static uint32_t lastDraw=0,lastStatus=0,lastRevision=0,maxDrawUs=0,uiStalls=0;
static uint32_t lastImuPoll=0,maxImuPollUs=0;
static StickS3Level::Reading drawnLevel;
static InactivityTimer inactivity;
static UsbHostAwake usbAwake;
static bool usbAutoOffInhibited=false;
static StickS3ShakeWake shakeWake;
static bool settingsSaveError=false;
static uint8_t settingsRow=0;
static uint8_t brightnessPercent=40;
static RpmEstimator::Mode rpmEstimator=RpmEstimator::DEFAULT_MODE;
static StickS3Battery battery;
static uint32_t lastBatteryPoll=0,maxBatteryPollUs=0,lastShutdownTry=0;
static bool batteryPolled=false;
static bool powerConfigValid=false;
static uint8_t powerConfig=0;
static Preferences powerPrefs;
static PowerDiagnostics::Image powerLog;
static bool powerLogReady=false,powerLogDirty=false;
static uint32_t powerLogTick=0,lastPowerSample=0,lastPowerSaveTry=0;
struct SleepReceipt {uint32_t magic;int64_t atUs;};
RTC_DATA_ATTR static SleepReceipt sleepReceipt={};
static uint8_t pm1WakeFlags=0;
static bool pm1WakeValid=false;
static StickS3MotionAcquisition imuAcquisition;
static MotionStore motionStore;
static LaunchMotion::Trace latestMotion,referenceMotion,demoMotion;
static bool motionPending=false,referenceError=false,motionDemo=false;
static uint64_t motionStart=0,motionEnd=0,lastLevelSampleUs=0;
static uint32_t motionDrops=0;
static LaunchFeedback launchFeedback;
static AnalogTachometer::Phase lastPhase=AnalogTachometer::Phase::Paused;
static bool lastFault=false;
using Action=StickS3Acquisition::Action;
using Snapshot=StickS3Acquisition::Snapshot;
static uint8_t backlightValue(){return (unsigned(brightnessPercent)*255+50)/100;}
static int64_t wallUs(){timeval t;gettimeofday(&t,nullptr);return int64_t(t.tv_sec)*1000000+t.tv_usec;}
static uint8_t powerFlags(){return (battery.charging?PowerDiagnostics::Charging:0)
  | (battery.chargeKnown?PowerDiagnostics::ChargeKnown:0) | (powerConfigValid && (powerConfig&0x10)?PowerDiagnostics::Led:0)
  | (extPower?PowerDiagnostics::Boost:0) | (tournamentMode?PowerDiagnostics::Tournament:0) | PowerDiagnostics::SensorRail;}
static void powerRecord(uint8_t event,uint8_t wake=0){PowerDiagnostics::append(powerLog,event,battery.voltageOk?battery.millivolts:0,
  powerFlags(),M5.Display.getBrightness(),ESP.getCpuFreqMHz(),wake);powerLogDirty=true;}
static bool savePowerLog(){
  // Bound retries after an NVS failure; repeated checkpoints keep the detector
  // in Settling and prevent subsequent pulls from being measured.
  lastPowerSaveTry=millis();
  if(!powerLogReady)return false;powerLog.checksum=PowerDiagnostics::hash(powerLog);
  const bool ok=powerPrefs.putBytes("log",&powerLog,sizeof(powerLog))==sizeof(powerLog);
  if(ok)powerLogDirty=false;return ok;
}
static void exportPowerLog(){
  Serial.printf("POWER_LOG schema=1 boots=%lu power_button_wakes=%lu shake_wakes=%lu other_wakes=%lu sleeps=%lu awake_s=%llu known_sleep_s=%llu unknown_sleep_intervals=%lu charging_awake_s=%llu led_awake_s=%llu boost_awake_s=%llu display_awake_s=%llu records=%lu storage_ready=%d unsaved=%d current_ma=unavailable\n",
    (unsigned long)powerLog.boots,(unsigned long)powerLog.powerButtonWakes,(unsigned long)powerLog.shakeWakes,
    (unsigned long)powerLog.otherWakes,(unsigned long)powerLog.sleeps,powerLog.awakeMs/1000,powerLog.sleepMs/1000,(unsigned long)powerLog.unknownSleepIntervals,
    powerLog.chargingMs/1000,powerLog.ledMs/1000,powerLog.boostMs/1000,powerLog.displayMs/1000,
    (unsigned long)powerLog.count,powerLogReady,powerLogDirty);
  for(unsigned i=0;i<powerLog.count;++i){const auto &r=powerLog.records[(powerLog.next+PowerDiagnostics::CAPACITY-powerLog.count+i)%PowerDiagnostics::CAPACITY];
    Serial.printf("POWER_RECORD tracked_s=%llu boot=%lu event=%u battery_mv=%u flags=0x%02x backlight=%u cpu_mhz=%u wake=%u\n",
      r.elapsedSeconds,(unsigned long)r.boot,r.event,r.batteryMv,r.flags,r.brightness,r.cpuMhz,r.wake);}
}
static void tickPowerLog(uint32_t now,const Snapshot &s){
  PowerDiagnostics::account(powerLog,now-powerLogTick,powerFlags(),M5.Display.getBrightness());powerLogTick=now;
  if(now-lastPowerSample>=60000){lastPowerSample=now;powerRecord(PowerDiagnostics::Sample);}
  if(powerLogReady && powerLogDirty && now-lastPowerSaveTry>=300000 && !motionPending && s.phase!=AnalogTachometer::Phase::Launch
    && acquisition.request(Action::IdleCheckpointBegin,s.launches)){
    if(!savePowerLog())Serial.println("POWER_LOG_NOTICE checkpoint_failed");acquisition.request(Action::CheckpointEnd);
  }
}


static const char *tournamentViewName() {
  switch(tournamentView) {
    case TournamentView::RecordingOnly:return "recording_only";
    default:return "rpm";
  }
}

static void status() {
  const Snapshot s=acquisition.snapshot();
  Serial.printf("STATUS v=%s board=StickS3 board_id=%d gpio=%u adc_ready=%d suspended=%d ext5v=%d width=%d height=%d rotation=%u samples=%llu delivered_sps=%.0f mean=%.1f min=%lu max=%lu last=%lu overflow_events=%lu read_errors=%lu adc_error=%s\n",
    VERSION,int(M5.getBoard()),s.pin,s.ready,s.suspended,extPower,M5.Display.width(),M5.Display.height(),
    unsigned(M5.Display.getRotation()),
    (unsigned long long)s.samples,s.rate,s.mean,(unsigned long)s.minimum,(unsigned long)s.maximum,
    (unsigned long)s.last,(unsigned long)s.overflows,(unsigned long)s.readErrors,esp_err_to_name(s.error));
  Serial.printf("RPM_STATUS state=%s valid=%d peak_rpm=%.1f live_peak=%.1f launches=%lu edges=%lu weak_rejected=%lu slow_rejected=%lu noise=%.1f amplitude=%.1f rearm_ms=%lu candidate_rpm=%.1f contrast=%.1f hysteresis=%.1f shape_rejected=%lu inconsistent=%lu rearm_extensions=%lu detector_us=%llu recorder_s=%lu min_mark=%.0f edge_fraction=%.2f\n",
    s.stateName(),s.valid,s.resultRpm,s.peakRpm,(unsigned long)s.launches,(unsigned long)s.edges,
    (unsigned long)s.weak,(unsigned long)s.slow,s.noise,s.amplitude,(unsigned long)s.rearmMs,
    s.candidateRpm,s.contrast,s.hysteresis,(unsigned long)s.shape,(unsigned long)s.inconsistent,
    (unsigned long)s.rearmExtensions,(unsigned long long)s.detectorUs,
    acquisition.storage()?60ul:0ul,StickS3SensorProfile::MIN_MARK,StickS3SensorProfile::EDGE_SWING_FRACTION);
  Serial.printf("RPM_ESTIMATORS selected=%s units=rpm three_turn_peak_rpm=%.1f single_turn_peak_rpm=%.1f confirmation_turns=3 max_rpm=30000 single_updates=%lu single_rejected=%lu\n",
    RpmEstimator::name(s.estimator),s.sustainedPeakRpm,s.singlePeakRpm,
    (unsigned long)s.singlePeakUpdates,(unsigned long)s.singlePeakRejected);
  Serial.printf("TOURNAMENT_STATUS enabled=%d display=%s persistent=0\n",tournamentMode,tournamentViewName());
  Serial.printf("PERF acquisition_core=0 ui_core=%d processing_pct=%.2f max_batch_us=%lu frame_budget_us=5120 max_read_gap_us=%lu stack_free=%lu invalid_frames=%lu lost_events=%lu max_draw_us=%lu ui_stalls=%lu stress=%d heap_free=%lu psram_free=%lu\n",
    xPortGetCoreID(),s.processingPercent,(unsigned long)s.maxBatchUs,(unsigned long)s.maxReadGapUs,
    (unsigned long)s.stackFree,(unsigned long)s.invalidFrames,(unsigned long)s.lostEvents,
    (unsigned long)maxDrawUs,(unsigned long)uiStalls,stress,
    (unsigned long)ESP.getFreeHeap(),(unsigned long)ESP.getFreePsram());
  const auto tilt=level.reading(millis());const float *acc=level.lastAccel();
  Serial.printf("LEVEL_STATUS imu_ready=%d imu_type=%d state=%s degrees=%.2f accel_g=%.3f,%.3f,%.3f samples=%lu rejected=%lu max_poll_us=%lu draw_buffer=%d\n",
    M5.Imu.isEnabled(),int(M5.Imu.getType()),tilt.name(),tilt.degrees,acc[0],acc[1],acc[2],
    (unsigned long)level.samples(),(unsigned long)level.rejected(),(unsigned long)maxImuPollUs,screenReady);
  const auto *session=practice.session();
  const uint32_t now=millis();
  Serial.printf("HISTORY_STATUS records=%u sessions=%u session=%lu session_pulls=%lu session_avg=%.1f generation=%lu pending=%d store_ready=%d save_errors=%lu saves=%lu max_save_us=%lu page=%s view=%u offset=%u demo=%d ui_stack_free=%lu\n",
    practice.size(),practice.sessions(),session?(unsigned long)session->number:0ul,
    session?(unsigned long)session->count:0ul,session?session->mean():0,
    (unsigned long)practice.generation(),practiceStore.pending(practice),practiceStore.ready(),
    (unsigned long)saveErrors,(unsigned long)saveCount,(unsigned long)maxSaveUs,
    diagnostics?"signal":historyPage?"history":"live",unsigned(historyView),historyOffset,demo,
    (unsigned long)uxTaskGetStackHighWaterMark(nullptr));
  const bool pendingHistory=practiceStore.pending(practice);
  const uint32_t pendingMs=pendingHistory && historyPendingSince?now-historyPendingSince:0;
  const uint32_t quietMs=now-lastAcceptedAt;
  const uint32_t flushDue=std::min(quietMs>=HISTORY_COALESCE_MS?0u:HISTORY_COALESCE_MS-quietMs,
    pendingMs>=HISTORY_MAX_PENDING_MS?0u:HISTORY_MAX_PENDING_MS-pendingMs);
  const uint32_t retryRemaining=saveError && now-lastSaveTry<HISTORY_SAVE_RETRY_MS?HISTORY_SAVE_RETRY_MS-(now-lastSaveTry):0;
  Serial.printf("HISTORY_PENDING unsaved_pulls=%lu pending_ms=%lu flush_due_ms=%lu coalesce_ms=%lu max_pending_ms=%lu retry_remaining_ms=%lu\n",
    (unsigned long)practiceStore.pendingCount(practice),(unsigned long)pendingMs,
    (unsigned long)(pendingHistory?flushDue:0),(unsigned long)HISTORY_COALESCE_MS,(unsigned long)HISTORY_MAX_PENDING_MS,(unsigned long)retryRemaining);
  Serial.printf("POWER_STATUS auto_off_s=%lu wake=shake sleep=imu_only sensor_rail=L2_off_in_battery_standby idle_s=%lu off_in_s=%lu battery_valid=%d battery_mv=%u battery_pct=%d charging=%s max_battery_poll_us=%lu auto_off_inhibited=%d\n",
    (unsigned long)(inactivity.timeout()/1000),(unsigned long)(inactivity.elapsed(now)/1000),(unsigned long)((inactivity.remaining(now)+999)/1000),
    battery.valid(now),unsigned(battery.millivolts),battery.valid(now)?battery.percent:-1,
    battery.chargeName(),(unsigned long)maxBatteryPollUs,usbAwake.inhibited(now));
  Serial.printf("USB_POWER host_sof=%d host_seen=%d auto_off_inhibited=%d reason=%s power_known=%d last_power_read_ok=%d source=0x%02x host_poll_ms=%lu power_poll_ms=%lu\n",
    usbAwake.sof(),usbAwake.remembered(),usbAwake.inhibited(now),usbAwake.reason(now),usbAwake.powerKnown(now),usbAwake.lastPowerReadOk(),usbAwake.powerBits(),
    (unsigned long)UsbHostAwake::HOST_POLL_MS,(unsigned long)UsbHostAwake::POWER_POLL_MS);
  Serial.printf("POWER_DETAIL uptime_s=%lu cpu_mhz=%lu backlight=%u pm1_cfg_valid=%d pm1_cfg=0x%02x led_enabled=%d current_measurement=unavailable\n",
    (unsigned long)(now/1000),(unsigned long)ESP.getCpuFreqMHz(),unsigned(M5.Display.getBrightness()),
    powerConfigValid,powerConfig,powerConfigValid?int(bool(powerConfig&0x10)):-1);
  const auto imu=imuAcquisition.snapshot();
  Serial.printf("MOTION_STATUS imu_core=0 imu_task=%d paired_samples=%lu accel_samples=%lu max_gap_us=%lu gaps=%lu max_poll_us=%lu stack_free=%lu gate_misses=%lu latest=%lu quality=%s pending=%d ref=%lu ref_rpm=%.1f ref_store_ready=%d ref_load_error=%d dropped=%lu demo=%d feedback=%d\n",
    imuAcquisition.running(),(unsigned long)imu.pairedSamples,(unsigned long)imu.accelSamples,
    (unsigned long)imu.maxGapUs,(unsigned long)imu.gaps,(unsigned long)imu.maxPollUs,(unsigned long)imu.stackFree,(unsigned long)imu.gateMisses,
    (unsigned long)latestMotion.number,LaunchMotion::name(latestMotion.quality),motionPending,
    (unsigned long)referenceMotion.number,referenceMotion.rpm,motionStore.ready(),referenceError,
    (unsigned long)motionDrops,motionDemo,launchFeedback.shown());
  Serial.printf("ORIENTATION_STATUS algorithm=VQF6D position=disabled absolute_heading=disabled ready=%d rest=%d updates=%lu resets=%lu max_fusion_us=%lu bias_dps=%.4f,%.4f,%.4f bias_sigma_dps=%.4f\n",
    imu.orientationReady,imu.rest,(unsigned long)imu.fusionSamples,(unsigned long)imu.fusionResets,
    (unsigned long)imu.maxFusionUs,imu.bias[0],imu.bias[1],imu.bias[2],imu.biasSigma);
}

// No serial reader is needed: isPlugged() uses IDF's SOF monitor, not CDC I/O.
static void pollUsbAwake(uint32_t now,const Snapshot &s,bool force=false) {
  if(!force && !usbAwake.hostPollDue(now))return;
  usbAwake.sampleHost(now,HWCDC::isPlugged());
  if(usbAwake.powerPollDue(now) && s.phase!=AnalogTachometer::Phase::Launch) {
    uint8_t source=0;bool ok=false;
    if(imuAcquisition.lock()) {
      // Checked PWR_SRC read: wrappers that return zero also hide I2C errors.
      ok=M5.Power.M5pm1.readRegister(0x04,&source,1);
      imuAcquisition.unlock();
    }
    usbAwake.samplePower(now,ok,source);
  }
  const bool inhibited=usbAwake.inhibited(now);
  if(inhibited!=usbAutoOffInhibited) {
    usbAutoOffInhibited=inhibited;
    // A disconnect starts a full ordinary battery timeout, not an overdue
    // timer accumulated during a long computer session. Touch only on edges.
    inactivity.touch(now);lastShutdownTry=0;
    Serial.printf("USB_AUTO_OFF inhibited=%d reason=%s sof=%d host_seen=%d power_known=%d source=0x%02x\n",
      inhibited,usbAwake.reason(now),usbAwake.sof(),usbAwake.remembered(),usbAwake.powerKnown(now),usbAwake.powerBits());
  }
}

static void pollBattery(uint32_t now,const Snapshot &s) {
  if(s.phase==AnalogTachometer::Phase::Launch || (batteryPolled && now-lastBatteryPoll<5000))return;
  if(!imuAcquisition.lock())return;
  batteryPolled=true;lastBatteryPoll=now;
  const int64_t started=esp_timer_get_time();
  uint16_t mv=0;uint8_t bits=0;
  const bool voltageRead=M5.Power.M5pm1.getBatteryVoltage(&mv);
  const bool chargeRead=M5.Power.M5pm1.getGPIOInputBits(&bits);
  powerConfigValid=M5.Power.M5pm1.readRegister(0x06,&powerConfig,1);
  imuAcquisition.unlock();
  battery.update(mv,voltageRead,chargeRead,bits,now);
  maxBatteryPollUs=std::max(maxBatteryPollUs,uint32_t(esp_timer_get_time()-started));
  if(historyPage && historyView==PracticeUI::View::Battery)dirty=true;
}

static void drawBattery(lgfx::LGFXBase &g,uint32_t now) {
  const int cx=g.width()/2;
  g.setTextDatum(top_center);g.setTextColor(TFT_WHITE,TFT_BLACK);
  g.drawString("Battery",cx,8,2);
  char line[32];
  const bool valid=battery.valid(now);
  if(valid)snprintf(line,sizeof(line),"%d%%",battery.percent);else snprintf(line,sizeof(line),"--");
  g.setTextColor(valid && battery.percent<=20?TFT_ORANGE:TFT_CYAN,TFT_BLACK);
  g.drawString(line,cx,43,4);
  g.drawRoundRect(29,96,74,25,3,TFT_DARKGREY);g.fillRect(103,103,4,11,TFT_DARKGREY);
  if(valid)g.fillRect(33,100,66*battery.percent/100,17,battery.percent<=20?TFT_ORANGE:TFT_CYAN);
  g.setTextColor(TFT_WHITE,TFT_BLACK);
  if(valid)snprintf(line,sizeof(line),"%.2f V",battery.millivolts/1000.0);else snprintf(line,sizeof(line),"Reading unavailable");
  g.drawString(line,cx,133,2);
  g.drawString(!battery.chargeKnown?"Charge status unknown":battery.charging?"Charging":"Not charging",cx,161,1);
  g.setTextColor(TFT_DARKGREY,TFT_BLACK);
  g.drawString("A next page  B main",cx,219,1);
}

static void drawSettings(lgfx::LGFXBase &g) {
  const int cx=g.width()/2;char text[24];
  g.setTextDatum(top_center);g.setTextColor(TFT_WHITE,TFT_BLACK);
  g.drawString("Settings",cx,8,2);
  g.drawRoundRect(4,32+settingsRow*53,g.width()-8,48,4,TFT_DARKGREY);
  g.setTextColor(settingsRow==0?TFT_CYAN:TFT_WHITE,TFT_BLACK);
  g.drawString("Sleep after",cx,35,2);
  snprintf(text,sizeof(text),"%u min",unsigned(inactivity.minutes()));g.drawString(text,cx,55,2);
  g.setTextColor(settingsRow==1?TFT_CYAN:TFT_WHITE,TFT_BLACK);
  g.drawString("RPM method",cx,88,2);g.drawString(RpmEstimator::label(rpmEstimator),cx,108,2);
  g.setTextColor(settingsRow==2?TFT_CYAN:TFT_WHITE,TFT_BLACK);
  g.drawString("Brightness",cx,141,2);
  snprintf(text,sizeof(text),"%u%%",unsigned(brightnessPercent));g.drawString(text,cx,161,2);
  g.setTextColor(settingsSaveError?TFT_ORANGE:TFT_DARKGREY,TFT_BLACK);
  g.drawString(settingsSaveError?"Try again when idle":"Saved on device",cx,190,1);
  g.drawString("Hold B select row",cx,205,1);g.drawString("Hold A change",cx,218,1);
  g.drawString("A next page  B main",cx,231,1);
}

static void exportSignal() {
  if(!acquisition.storage() || !acquisition.request(Action::Suspend)) {
    Serial.println("RAW_ERROR acquisition_suspend_failed");return;
  }
  const Snapshot s=acquisition.snapshot();
  if(s.ringCount) {
    Serial.printf("FLIGHT_EXPORT samples=%lu end_detector_us=%llu state=%s launches=%lu gpio=%u display_blanking=0\n",
      (unsigned long)s.ringCount,(unsigned long long)s.detectorUs,s.stateName(),(unsigned long)s.launches,s.pin);
    opticalTransferRaw(acquisition.storage(),StickS3Acquisition::RING_SAMPLES,s.ringFirst,s.ringCount,
      int64_t(s.ringCount)*1000000/ANALOG_SAMPLE_HZ,0,0,true,ESP_OK,false);
  } else Serial.println("RAW_ERROR no_flight_record");
  if(!acquisition.request(Action::Resume))Serial.println("ADC_ERROR resume_failed");
  dirty=true;
}

static void drawLiveLevel(lgfx::LGFXBase &view,int cx) {
    const int cy=172,radius=31;
    view.setTextColor(TFT_DARKGREY,TFT_BLACK);
    view.drawCircle(cx,cy,radius,TFT_DARKGREY);
    view.drawFastHLine(cx-radius+3,cy,2*radius-5,TFT_DARKGREY);
    view.drawFastVLine(cx,cy-radius+3,2*radius-5,TFT_DARKGREY);
    view.drawCircle(cx,cy,6,TFT_DARKGREY);
    drawnLevel=level.reading(millis());
    if(drawnLevel.valid()) {
      const auto color=drawnLevel.degrees<=2?TFT_CYAN:TFT_ORANGE;
      view.fillCircle(cx+lroundf(drawnLevel.right*25),cy+lroundf(drawnLevel.down*25),5,color);
      char angle[20];snprintf(angle,sizeof(angle),"%.1f deg",drawnLevel.degrees);
      view.setTextColor(color,TFT_BLACK);view.drawString(angle,cx,207,2);
    } else {
      view.drawString("--",cx,207,2);
    }
}

static void draw(const Snapshot &s) {
  const int64_t started=esp_timer_get_time();
  const uint32_t replayFrameElapsed=launchFeedback.replayElapsed(millis());
  auto &view=screenReady?static_cast<lgfx::LGFXBase &>(screen):static_cast<lgfx::LGFXBase &>(M5.Display);
  if(!screenReady){acquisition.displayBoundary(true);M5.Display.startWrite();}
  view.fillScreen(TFT_BLACK);
  const int cx=view.width()/2;
  view.setTextDatum(top_center);
  view.setTextColor(TFT_WHITE,TFT_BLACK);
  if(!tournamentMode)view.drawString(newSessionAt && millis()-newSessionAt<1500?"New session ready":practiceStore.pending(practice)?"Unsaved launch":"LaunchLab Mini",cx,8,2);
  view.setTextColor(s.ready && !s.signalFault?TFT_GREEN:TFT_ORANGE,TFT_BLACK);
  if(!tournamentMode)view.drawString(s.stateName(),cx,32,2);
  view.setTextColor(TFT_WHITE,TFT_BLACK);
  if(tournamentMode) {
    if(tournamentView==TournamentView::RecordingOnly) {
      // A static card keeps launch results out of the competitor's view.
      view.setTextColor(TFT_RED,TFT_BLACK);
      view.drawString("RECORDING",cx,84,2);
      view.drawString("ONLY",cx,108,4);
    } else {
      char rpm[16];
      if(s.valid)snprintf(rpm,sizeof(rpm),"%.0f",s.resultRpm);
      else snprintf(rpm,sizeof(rpm),"--");
      const int rpmFont=view.textWidth(rpm,&fonts::Font6)<=view.width()-8?6:4;
      view.drawString(rpm,cx,86,rpmFont);
      view.drawString("RPM",cx,137,2);
    }
  } else if(diagnostics) {
    view.setTextDatum(top_left);
    char line[64];
    snprintf(line,sizeof(line),"AO G%u: %lu",s.pin,(unsigned long)s.last);
    view.drawString(line,8,64,2);
    snprintf(line,sizeof(line),"Range %lu-%lu",(unsigned long)s.minimum,(unsigned long)s.maximum);
    view.drawString(line,8,93,2);
    snprintf(line,sizeof(line),"%.0f samples/s",s.rate);
    view.drawString(line,8,122,2);
  } else if(historyPage) {
    view.fillScreen(TFT_BLACK);
    if(historyView==PracticeUI::View::Settings)drawSettings(view);
    else if(historyView==PracticeUI::View::Battery)drawBattery(view,millis());
    else PracticeUI::draw(view,demo?demoPractice:practice,historyView,historyOffset,demo,saveError,practiceStore.pending(practice));
  } else if(launchFeedback.shown()) {
    view.fillScreen(TFT_BLACK);
    MotionUI::feedback(view,motionDemo?demoMotion:latestMotion,
      motionPending && !motionDemo,motionDemo,MotionReplay::playbackProgress(motionDemo?demoMotion:latestMotion,replayFrameElapsed),!motionDemo && practiceStore.pending(practice));
  } else {
    char rpm[16];
    if(s.valid)snprintf(rpm,sizeof(rpm),"%.0f",s.resultRpm);
    else snprintf(rpm,sizeof(rpm),"--");
    view.setTextDatum(top_center);
    // Keep large values inside the narrow portrait width as well.
    const int rpmFont=view.textWidth(rpm,&fonts::Font6)<=view.width()-8?6:4;
    view.drawString(rpm,cx,53,rpmFont);
    view.drawString("RPM",cx,100,2);
    drawLiveLevel(view,cx);
  }
  if(!tournamentMode && (diagnostics || (!historyPage && !launchFeedback.shown()))) {
    view.setTextDatum(top_center);view.setTextColor(TFT_DARKGREY,TFT_BLACK);
    view.drawString("A recent  B history",cx,231,1);
  }
  if(screenReady){acquisition.displayBoundary(true);M5.Display.startWrite();screen.pushSprite(0,0);}
  M5.Display.endWrite();
  acquisition.displayBoundary(false);
  launchFeedback.replayPresented(millis(),!tournamentMode && !diagnostics && !historyPage &&
    (!motionPending || motionDemo) && (motionDemo?demoMotion:latestMotion).valid() && (motionDemo?demoMotion:latestMotion).fused,replayFrameElapsed);
  maxDrawUs=std::max(maxDrawUs,uint32_t(esp_timer_get_time()-started));
}

static void pollLevel(uint32_t now) {
  if(imuAcquisition.running()) {
    const auto sample=imuAcquisition.snapshot();
    if(sample.fusedUs && sample.fusedUs!=lastLevelSampleUs) {
      lastLevelSampleUs=sample.fusedUs;
      if(sample.orientationReady)level.feed(sample.gravity[0],sample.gravity[1],sample.gravity[2],uint32_t(sample.fusedUs/1000));
      else level.feed(0,0,0,uint32_t(sample.fusedUs/1000));
    }
    return;
  }
  if(!M5.Imu.isEnabled() || now-lastImuPoll<20)return;
  lastImuPoll=now;const int64_t started=esp_timer_get_time();
  // update's returned accel bit establishes freshness; cached data is not a new sample.
  if(M5.Imu.update() & m5::IMU_Class::sensor_mask_accel) {
    const auto data=M5.Imu.getImuData();
    level.feed(data.accel.x,data.accel.y,data.accel.z,millis());
  }
  maxImuPollUs=std::max(maxImuPollUs,uint32_t(esp_timer_get_time()-started));
}

static void exportScreen() {
  if(!screenReady){Serial.println("SNAP_ERROR no_draw_buffer");return;}
  // Export the last displayed frame, including its frozen level during a pull.
  const unsigned width=screen.width(),height=screen.height();
  Serial.printf("SNAP %u %u %u\n",width,height,width*height*2);
  uint8_t row[240*2];
  for(unsigned y=0;y<height;++y) {
    for(unsigned x=0;x<width;++x) {
      const uint16_t pixel=screen.readPixel(x,y);row[x*2]=pixel>>8;row[x*2+1]=pixel;
    }
    Serial.write(row,width*2);
  }
}

static void toggleFeedback() {
  if(tournamentMode)return;
  historyPage=diagnostics=motionDemo=demo=false;
  launchFeedback.toggle(millis(),latestMotion.number!=0);dirty=true;
  Serial.printf("MAIN_FEEDBACK shown=%d reason=button t_ms=%lu\n",launchFeedback.shown(),(unsigned long)millis());
}

static void toggleHistory() {
  if(tournamentMode) {
    tournamentView=TournamentView((unsigned(tournamentView)+1)%2);
    dirty=true;
    Serial.printf("TOURNAMENT_VIEW display=%s reason=button_B\n",tournamentViewName());
    return;
  }
  launchFeedback.clear();
  if(demo){demo=false;historyPage=false;}else historyPage=!historyPage;
  motionDemo=false;diagnostics=false;historyOffset=0;dirty=true;
}
static void nextView() {
  historyView=PracticeUI::next(historyView);historyOffset=0;dirty=true;
}
static void prepareMotion(const Snapshot &event) {
  lastAcceptedAt=millis();if(!historyPendingSince)historyPendingSince=lastAcceptedAt;
  if(motionPending)++motionDrops;
  latestMotion={};latestMotion.number=practice.recent()->number;latestMotion.rpm=event.resultRpm;
  motionStart=event.burstStartHostUs;motionEnd=event.burstEndHostUs;motionPending=true;
  historyPage=diagnostics=motionDemo=demo=false;
  if(!tournamentMode)launchFeedback.show(millis());
  dirty=true;
}
static void finishMotion() {
  if(!motionPending)return;
  const uint64_t now=esp_timer_get_time();const auto imu=imuAcquisition.snapshot();
  if(!LaunchMotion::captureReady(now,motionEnd,imu.fusedUs))return;
  imuAcquisition.capture(motionStart,motionEnd,latestMotion.rpm,latestMotion.number,latestMotion);
  motionPending=false;dirty=true;
  if(launchFeedback.shown())launchFeedback.show(millis());
  Serial.printf("MAIN_FEEDBACK shown=%d reason=result t_ms=%lu\n",launchFeedback.shown(),(unsigned long)millis());
  Serial.printf("MOTION_RESULT launch=%lu quality=%s points=%u duration_ms=%lu rpm=%.1f stationary_bias=%d\n",
    (unsigned long)latestMotion.number,LaunchMotion::name(latestMotion.quality),latestMotion.count,
    (unsigned long)latestMotion.durationMs,latestMotion.rpm,latestMotion.stationaryBias);
  Serial.printf("RECAP_LEVEL launch=%lu start_valid=%d start_xy=%.4f,%.4f end_valid=%d end_xy=%.4f,%.4f\n",
    (unsigned long)latestMotion.number,latestMotion.startLevel.valid(),latestMotion.startLevel.right,latestMotion.startLevel.down,
    latestMotion.endLevel.valid(),latestMotion.endLevel.right,latestMotion.endLevel.down);
}
static void exportMotion() {
  for(const auto *t:{&referenceMotion,&latestMotion}) {
    const char *role=t==&referenceMotion?"reference":"latest";
    Serial.printf("MOTION_EXPORT role=%s number=%lu rpm=%.3f quality=%s count=%u duration_ms=%lu stationary_bias=%d fused=%d\n",role,
      (unsigned long)t->number,t->rpm,LaunchMotion::name(t->quality),t->count,(unsigned long)t->durationMs,t->stationaryBias,t->fused);
    if(t->valid())for(unsigned i=0;i<t->count;++i) {
      const auto &p=t->points[i];Serial.printf("MOTION_POINT role=%s t_ms=%d accel_change_g=%.3f,%.3f,%.3f gyro_dps=%.1f,%.1f,%.1f q=%.5f,%.5f,%.5f,%.5f\n",
        role,p.ms,p.a[0]*.001f,p.a[1]*.001f,p.a[2]*.001f,p.g[0]*.1f,p.g[1]*.1f,p.g[2]*.1f,
        p.q[0]/16384.0f,p.q[1]/16384.0f,p.q[2]/16384.0f,p.q[3]/16384.0f);
    }
    auto replay=std::unique_ptr<MotionReplay::Replay>(new(std::nothrow) MotionReplay::Replay);
    if(replay && replay->build(*t)) {
      Serial.printf("REPLAY_EXPORT role=%s number=%lu mode=rotation_only position=disabled absolute_heading=disabled count=%u\n",
        role,(unsigned long)t->number,MotionReplay::Replay::COUNT);
      for(unsigned i=0;i<MotionReplay::Replay::COUNT;++i) {
        const auto &q=replay->pose[i];Serial.printf("REPLAY_POINT role=%s t_ms=%d gravity_aligned_q=%.5f,%.5f,%.5f,%.5f\n",role,
          replay->ms[i],q.w,q.x,q.y,q.z);
      }
    }
  }
}
static void newSession() {
  practice.newSession();newSessionAt=millis();demo=false;diagnostics=false;historyPage=false;dirty=true;
  Serial.println("HISTORY_SESSION next accepted launch starts a new session");
}
static void changeSleepTimeout() {
  const auto s=acquisition.snapshot();
  if(motionPending || !acquisition.request(Action::IdleCheckpointBegin,s.launches)) {
    settingsSaveError=true;dirty=true;Serial.println("SLEEP_SETTING wait_for_idle");return;
  }
  const uint8_t minutes=InactivityTimer::nextMinutes(inactivity.minutes());
  const bool saved=prefs.putUChar("sleep_min",minutes)==1;
  if(saved)inactivity.setMinutes(minutes);
  settingsSaveError=!saved;
  if(!acquisition.request(Action::CheckpointEnd))Serial.println("SLEEP_SETTING_ERROR acquisition_resume");
  dirty=true;
  Serial.printf("SLEEP_SETTING saved=%d minutes=%u\n",saved,unsigned(inactivity.minutes()));
}
static void changeRpmEstimator() {
  const auto s=acquisition.snapshot();
  if(motionPending || !acquisition.request(Action::IdleCheckpointBegin,s.launches)) {
    settingsSaveError=true;dirty=true;Serial.println("RPM_SETTING wait_for_idle");return;
  }
  const auto next=RpmEstimator::next(rpmEstimator);
  bool saved=RpmEstimatorSetting::save(prefs,next);
  if(saved && !acquisition.request(Action::Estimator,uint8_t(next))) {
    saved=false;
    if(!RpmEstimatorSetting::save(prefs,rpmEstimator))Serial.println("RPM_SETTING_ERROR preference_rollback_failed");
  }
  if(saved) {
    rpmEstimator=next;practice.newSession();launchFeedback.clear();
  }
  settingsSaveError=!saved;
  if(!acquisition.request(Action::CheckpointEnd))Serial.println("RPM_SETTING_ERROR acquisition_resume");
  dirty=true;
  Serial.printf("RPM_SETTING saved=%d selected=%s next_pull_new_session=%d\n",saved,RpmEstimator::name(rpmEstimator),saved);
}
static void changeBrightness() {
  const auto s=acquisition.snapshot();
  if(motionPending || !acquisition.request(Action::IdleCheckpointBegin,s.launches)) {
    settingsSaveError=true;dirty=true;return;
  }
  const uint8_t next=brightnessPercent>=100?10:brightnessPercent+10;
  const bool saved=prefs.putUChar("bright_pct",next)==1;
  if(saved){brightnessPercent=next;M5.Display.setBrightness(backlightValue());}
  settingsSaveError=!saved;dirty=true;
  if(!acquisition.request(Action::CheckpointEnd))Serial.println("BRIGHTNESS_SETTING_ERROR acquisition_resume");
  Serial.printf("BRIGHTNESS_SETTING saved=%d percent=%u backlight=%u\n",saved,brightnessPercent,backlightValue());
}
static void logLaunchMetrics(const Snapshot &s) {
  const auto *record=practice.recent();if(!record)return;
  Serial.printf("LAUNCH_METRICS number=%lu session=%lu selected_estimator=%s selected_rpm=%.1f three_turn_peak_rpm=%.1f single_turn_peak_rpm=%.1f units=rpm\n",
    (unsigned long)record->number,(unsigned long)record->session,RpmEstimator::name(s.estimator),
    s.resultRpm,s.sustainedPeakRpm,s.singlePeakRpm);
}
static void holdA() {
  if(tournamentMode || (!historyPage && !diagnostics)) {
    tournamentMode=!tournamentMode;
    if(tournamentMode)tournamentView=TournamentView::RecordingOnly;
    historyPage=diagnostics=motionDemo=demo=false;
    launchFeedback.clear();dirty=true;
    Serial.printf("TOURNAMENT_MODE enabled=%d reason=hold_A\n",tournamentMode);
  } else if(historyView==PracticeUI::View::Settings){
    if(settingsRow==1)changeRpmEstimator();else if(settingsRow==2)changeBrightness();else changeSleepTimeout();
  }
  else newSession();
}
static void browseOlder() {
  if(tournamentMode)return;
  if(!historyPage){diagnostics=!diagnostics;dirty=true;return;}
  if(historyView==PracticeUI::View::Settings){settingsRow=(settingsRow+1)%3;dirty=true;return;}
  if(historyView==PracticeUI::View::Battery)return;
  const auto &h=demo?demoPractice:practice;
  const unsigned total=PracticeUI::count(h,historyView),step=PracticeUI::window(historyView);
  historyOffset=historyOffset+step<total?historyOffset+step:0;dirty=true;
}
static void previewHistory() {
  demo=!demo;diagnostics=false;historyPage=demo;historyView=PracticeUI::View::Recent;historyOffset=0;
  if(demo && !demoPractice.size()) {
    uint32_t count=0;
    for(unsigned session=0;session<18;++session) {
      demoPractice.newSession();
      for(unsigned i=0;i<12;++i) {
        const float rpm=4200+session*130+float(int(i%5)-2)*260+i*35;
        demoPractice.accept(++count,true,rpm,session*900000+i*20000);
      }
    }
  }
  Serial.printf("HISTORY_DEMO enabled=%d synthetic display only; saved history unchanged\n",demo);dirty=true;
}
static void exportHistory() {
  Serial.printf("HISTORY_EXPORT records=%u sessions=%u metric=peak_rpm order=oldest_first\n",practice.size(),practice.sessions());
  for(unsigned i=practice.size();i>0;--i) {
    const auto &r=*practice.recent(i-1);
    Serial.printf("HISTORY_LAUNCH number=%lu session=%lu rpm=%.3f session_seconds=%lu\n",
      (unsigned long)r.number,(unsigned long)r.session,r.rpm,(unsigned long)r.seconds);
  }
  for(unsigned i=practice.sessions();i>0;--i) {
    const auto &s=*practice.session(i-1);
    Serial.printf("HISTORY_SESSION number=%lu pulls=%lu average_rpm=%.3f best_rpm=%.3f seconds=%lu\n",
      (unsigned long)s.number,(unsigned long)s.count,s.mean(),s.best,(unsigned long)s.seconds);
  }
}
static void saveHistory(uint32_t now,const Snapshot &s) {
  const bool history=practiceStore.pending(practice) && practiceStore.ready();
  // Failed writes must leave enough uninterrupted quiet for detector rearm.
  const uint32_t retryMs=saveError?HISTORY_SAVE_RETRY_MS:1000;
  if(motionPending || !history || now-lastSaveTry<retryMs || s.phase==AnalogTachometer::Phase::Launch)return;
  // Coalesce a rapid practice bout instead of resetting fusion after each pull.
  // Pending RAM history is flushed once the newest accepted pull has been idle.
  const bool overdue=historyPendingSince && now-historyPendingSince>=HISTORY_MAX_PENDING_MS;
  if(!overdue && now-lastAcceptedAt<HISTORY_COALESCE_MS)return;
  // Protect presentation through the final replay frame; the ordinary save
  // path resumes afterward, on hidden/invalid recap, or at its 5 s expiry.
  if(!tournamentMode && !diagnostics && !historyPage && launchFeedback.replayStarted() &&
     MotionReplay::playbackNeedsFrame(motionDemo?demoMotion:latestMotion,launchFeedback.replayElapsed(now),launchFeedback.lastReplayElapsed()))return;
  if(s.phase!=AnalogTachometer::Phase::Ready && s.phase!=AnalogTachometer::Phase::Paused)return;
  lastSaveTry=now;
  if(!acquisition.request(Action::HistoryIdleCheckpointBegin,s.launches))return;
  const int64_t started=esp_timer_get_time();
  const bool saved=practiceStore.save(practice);
  maxSaveUs=std::max(maxSaveUs,uint32_t(esp_timer_get_time()-started));
  if(saved){++saveCount;saveError=false;historyPendingSince=0;}else {++saveErrors;saveError=true;}
  if(!acquisition.request(Action::CheckpointEnd))Serial.println("HISTORY_ERROR ADC checkpoint resume failed");
  lastSaveTry=millis();
  Serial.printf("HISTORY_SAVE ok=%d generation=%lu duration_us=%lu\n",saved,
    (unsigned long)practice.generation(),(unsigned long)(esp_timer_get_time()-started));
  dirty=true;
}

static void autoPowerOff(uint32_t now,const Snapshot &s) {
  if(usbAwake.inhibited(now))return;
  if(motionPending || !inactivity.due(now,s.phase==AnalogTachometer::Phase::Launch) ||
     (lastShutdownTry && now-lastShutdownTry<60000))return;
  // Recheck immediately at the timer boundary; periodic polling alone could
  // leave a just-attached computer unnoticed for up to 250ms.
  pollUsbAwake(now,s,true);
  if(usbAwake.inhibited(now) || !inactivity.due(now,s.phase==AnalogTachometer::Phase::Launch))return;
  lastShutdownTry=now;
  if(!acquisition.request(Action::ShutdownBegin,s.launches))return;
  // Finish any queued accepted result before saving; the owner is now stopped.
  Snapshot event;
  bool newPull=false;
  while(acquisition.takeEvent(event))if(practice.accept(event.launches,event.valid,event.resultRpm,now)){prepareMotion(event);logLaunchMetrics(event);newPull=true;}
  if(newPull) {
    inactivity.touch(now);lastShutdownTry=0;dirty=true;
    if(!acquisition.request(Action::CheckpointEnd))acquisition.request(Action::Pin,s.pin);
    return;
  }
  if(practiceStore.pending(practice) && (!practiceStore.ready() || !practiceStore.save(practice))) {
    saveError=true;++saveErrors;dirty=true;
    Serial.println("POWER_OFF_DEFERRED history_save_failed; retry in 60s");
    if(!acquisition.request(Action::CheckpointEnd))acquisition.request(Action::Pin,s.pin);
    lastSaveTry=millis();
    return;
  }
  historyPendingSince=0;saveError=false;
  // A host may attach while the forced history flush is blocking.
  pollUsbAwake(millis(),acquisition.snapshot(),true);
  if(usbAwake.inhibited(millis())) {
    if(!acquisition.request(Action::CheckpointEnd))acquisition.request(Action::Pin,s.pin);
    return;
  }
  Serial.printf("POWER_OFF reason=inactivity idle_ms=%lu records=%u saved=1\n",
    (unsigned long)inactivity.elapsed(now),practice.size());
  Serial.flush();
  if(imuAcquisition.lock()) {
    bool usbCancelled=false;
    if(shakeWake.arm()) {
      const WakeUi::State state{tournamentMode,historyPage && !demo && !diagnostics,
        uint8_t(tournamentView),uint8_t(historyView)};
      if(prefs.putUInt("wake_ui",WakeUi::encode(state))==sizeof(uint32_t)) {
        // Keep the overwritten ring entry so a USB-cancelled attempt is not
        // counted or exported as an actual standby.
        const uint32_t previousPowerNext=powerLog.next,previousPowerCount=powerLog.count;
        const auto previousPowerRecord=powerLog.records[previousPowerNext];
        ++powerLog.sleeps;powerLog.pendingSleep=1;powerRecord(PowerDiagnostics::Sleep);
        if(!savePowerLog())Serial.println("POWER_LOG_NOTICE sleep_checkpoint_failed");
        sleepReceipt={PowerDiagnostics::MAGIC,wallUs()};
        M5.Display.setBrightness(0);M5.Display.sleep();
        Serial.printf("SHAKE_SLEEP timeout_s=%lu sensor_rail=L2_off_on_battery wake=imu_motion mode=imu_only\n",(unsigned long)(inactivity.timeout()/1000));Serial.flush();
        // Flash/USB flushing above can outlast the earlier host check. This
        // last O(1) SOF read is safe while holding the IMU mutex; do not call
        // pollUsbAwake here because it can attempt that mutex again.
        if(HWCDC::isPlugged()) {
          usbCancelled=true;usbAwake.sampleHost(millis(),true);usbAutoOffInhibited=true;
          inactivity.touch(millis());lastShutdownTry=0;
          --powerLog.sleeps;powerLog.next=previousPowerNext;powerLog.count=previousPowerCount;
          powerLog.records[previousPowerNext]=previousPowerRecord;powerLogDirty=true;
          Serial.println("POWER_OFF_DEFERRED usb_host_attached_before_sleep");
        } else shakeWake.sleep();
        sleepReceipt.magic=0;powerLog.pendingSleep=0;
        savePowerLog();
        M5.Display.wakeup();M5.Display.setBrightness(backlightValue());
        if(!prefs.remove("wake_ui"))Serial.println("WAKE_UI_NOTICE failed_sleep_marker_clear");
      } else Serial.println("POWER_OFF_DEFERRED wake_mode_save_failed");
    }
    const bool restored=shakeWake.restore();
    M5.Power.setExtOutput(extPower);imuAcquisition.unlock();
    Serial.printf("POWER_OFF_DEFERRED reason=%s restored=%d retry_s=%u\n",usbCancelled?"usb_host_attached":"shake_sleep_failed",restored,usbCancelled?0:60);
  } else Serial.println("POWER_OFF_DEFERRED imu_bus_busy");
  if(!acquisition.request(Action::CheckpointEnd))acquisition.request(Action::Pin,s.pin);
}

static void checkStorage() {
  // Explicit USB bench diagnostic. Scratch measurements never enter practice.
  const auto state=acquisition.snapshot();
  if(motionPending || !acquisition.request(Action::IdleCheckpointBegin,state.launches)) {
    Serial.println("HISTORY_CHECK_ERROR wait until capture finishes");return;
  }
  Preferences scratch;scratch.begin("ll-prac-qa",false);
  // Only this diagnostic owns these scratch keys; recover an interrupted bench.
  if(scratch.isKey("history0"))scratch.remove("history0");
  if(scratch.isKey("history1"))scratch.remove("history1");
  bool ok=!scratch.isKey("history0") && !scratch.isKey("history1");
  const bool clean=ok;
  auto h=std::unique_ptr<PracticeHistory>(new(std::nothrow) PracticeHistory);
  auto store=std::unique_ptr<PracticeStore>(new(std::nothrow) PracticeStore);
  uint32_t maximum=0;unsigned writes=0;
  ok=ok && h && store && store->begin(*h,"ll-prac-qa");
  for(unsigned i=1;ok && i<=36;++i) {
    if(i%6==1)h->newSession();
    h->accept(i,true,5000+i*30,i*20000);
    const int64_t started=esp_timer_get_time();ok=store->save(*h);
    if(ok)++writes;
    maximum=std::max(maximum,uint32_t(esp_timer_get_time()-started));
    auto restored=std::unique_ptr<PracticeHistory>(new(std::nothrow) PracticeHistory);
    auto reader=std::unique_ptr<PracticeStore>(new(std::nothrow) PracticeStore);
    ok=ok && restored && reader && reader->begin(*restored,"ll-prac-qa") &&
      restored->generation()==h->generation() && restored->size()==h->size() &&
      restored->session()->mean()==h->session()->mean() && restored->recent()->rpm==h->recent()->rpm;
  }
  if(clean) {
    if(scratch.isKey("history0"))ok=scratch.remove("history0") && ok;
    if(scratch.isKey("history1"))ok=scratch.remove("history1") && ok;
    ok=ok && !scratch.isKey("history0") && !scratch.isKey("history1");
  }
  const bool resumed=acquisition.request(Action::CheckpointEnd);
  Serial.printf("HISTORY_CHECK ok=%d writes=%u max_write_us=%lu scratch_clean=%d resumed=%d actual_records=%u\n",
    ok,writes,(unsigned long)maximum,clean,resumed,practice.size());dirty=true;
}

static void checkMotionStorage() {
  const auto state=acquisition.snapshot();
  if(motionPending || !acquisition.request(Action::IdleCheckpointBegin,state.launches)) {
    Serial.println("MOTION_CHECK_ERROR wait until capture finishes");return;
  }
  Preferences scratch;scratch.begin("ll-mot-qa",false);
  for(const char *key:{"ref0","ref1"})if(scratch.isKey(key))scratch.remove(key);
  const bool clean=!scratch.isKey("ref0") && !scratch.isKey("ref1");
  auto t=std::unique_ptr<LaunchMotion::Trace>(new(std::nothrow) LaunchMotion::Trace);
  auto restored=std::unique_ptr<LaunchMotion::Trace>(new(std::nothrow) LaunchMotion::Trace);
  auto store=std::unique_ptr<MotionStore>(new(std::nothrow) MotionStore);
  bool ok=clean && t && restored && store && store->begin(*restored,"ll-mot-qa");
  unsigned writes=0;uint32_t maximum=0;
  if(t)MotionUI::makeDemo(*t,true);
  for(unsigned i=1;ok && i<=16;++i) {
    t->number=i;t->rpm=5000+i*50;const int64_t started=esp_timer_get_time();ok=store->save(*t);
    if(ok)++writes;maximum=std::max(maximum,uint32_t(esp_timer_get_time()-started));
    auto reader=std::unique_ptr<MotionStore>(new(std::nothrow) MotionStore);
    ok=ok && reader && reader->begin(*restored,"ll-mot-qa") && restored->number==i && restored->rpm==t->rpm;
  }
  bool cleaned=clean;
  if(clean)for(const char *key:{"ref0","ref1"})if(scratch.isKey(key))cleaned=scratch.remove(key) && cleaned;
  cleaned=cleaned && !scratch.isKey("ref0") && !scratch.isKey("ref1");
  const bool resumed=acquisition.request(Action::CheckpointEnd);
  Serial.printf("MOTION_CHECK ok=%d writes=%u bytes=%u max_write_us=%lu scratch_clean=%d resumed=%d actual_records=%u actual_ref=%lu\n",
    ok,writes,unsigned(LaunchMotion::IMAGE_BYTES),(unsigned long)maximum,cleaned,resumed,practice.size(),(unsigned long)referenceMotion.number);
  dirty=true;
}

void setup() {
  const auto wakeCause=esp_sleep_get_wakeup_cause();
  const int64_t sleepEnded=wallUs();
  Serial.begin(115200);
  Serial.setTxTimeoutMs(10);
  // Set once before either acquisition task starts. Keep ADC, USB and SPI
  // peripheral clocks unchanged; do not switch frequency during a launch.
  const bool clockSet=setCpuFrequencyMhz(LAUNCHLAB_CPU_MHZ);
  const bool clockOk=clockSet && getCpuFrequencyMhz()==LAUNCHLAB_CPU_MHZ && getApbFrequency()==80000000;
  if(!clockOk)setCpuFrequencyMhz(240);
  Serial.printf("CPU_POLICY requested_mhz=%u actual_mhz=%lu apb_hz=%lu fallback=%d\n",
    unsigned(LAUNCHLAB_CPU_MHZ),(unsigned long)getCpuFrequencyMhz(),(unsigned long)getApbFrequency(),!clockOk);
  auto cfg=M5.config();
  cfg.fallback_board=m5::board_t::board_M5StickS3;
  cfg.internal_mic=cfg.internal_spk=cfg.internal_rtc=false;cfg.internal_imu=true;
  cfg.external_imu=cfg.external_rtc=false;cfg.output_power=false;
  M5.begin(cfg);
  M5.Ex_I2C.release();
  pm1WakeValid=M5.Power.M5pm1.readRegister(0x05,&pm1WakeFlags,1);
  M5.Power.M5pm1.clearWakeSource();
  if(!shakeWake.clear())Serial.println("SHAKE_WAKE_NOTICE startup_disarm_failed");
  prefs.begin("launchlab-mini",false);
  powerLogReady=powerPrefs.begin("ll-power",false);
  PowerDiagnostics::fresh(powerLog);
  if(powerLogReady && powerPrefs.isKey("log")){
    PowerDiagnostics::Image loaded;
    if(powerPrefs.getBytesLength("log")==sizeof(loaded) && powerPrefs.getBytes("log",&loaded,sizeof(loaded))==sizeof(loaded)
      && PowerDiagnostics::valid(loaded))powerLog=loaded;
    else {powerLogReady=false;Serial.println("POWER_LOG_NOTICE invalid_existing_log_retained");}
  }
  ++powerLog.boots;
  const bool wakingFromStandby=powerLog.pendingSleep;
  uint8_t loggedWake=pm1WakeValid?pm1WakeFlags:0;
  if(wakingFromStandby && ((pm1WakeValid && (pm1WakeFlags&0x20)) || wakeCause==ESP_SLEEP_WAKEUP_EXT0))++powerLog.shakeWakes;
  else if(pm1WakeValid && (pm1WakeFlags&0x0c))++powerLog.powerButtonWakes;
  else ++powerLog.otherWakes;
  if(wakingFromStandby) {
    if(wakeCause!=ESP_SLEEP_WAKEUP_UNDEFINED && sleepReceipt.magic==PowerDiagnostics::MAGIC
      && sleepEnded>=sleepReceipt.atUs && sleepEnded-sleepReceipt.atUs<366LL*24*3600*1000000)
      powerLog.sleepMs+=uint64_t(sleepEnded-sleepReceipt.atUs)/1000;
    else ++powerLog.unknownSleepIntervals; // PM1 battery shutdown loses ESP32 RTC time.
  }
  powerLog.pendingSleep=0;sleepReceipt.magic=0;
  if(prefs.isKey("wake_ui")) {
    WakeUi::State state;
    const bool valid=WakeUi::decode(prefs.getUInt("wake_ui",0),uint8_t(PracticeUI::View::Settings),state);
    const bool consumed=prefs.remove("wake_ui");
    if(valid && consumed) {
      tournamentMode=state.tournament;tournamentView=TournamentView(state.tournamentView);
      historyPage=state.history;historyView=PracticeUI::restoredView(state.historyView);
    }
    Serial.printf("WAKE_UI_RESTORE valid=%d consumed=%d tournament=%d display=%s history=%d page=%u\n",
      valid,consumed,tournamentMode,tournamentViewName(),historyPage,unsigned(historyView));
  }
  if(!RpmEstimatorSetting::load(prefs,rpmEstimator))Serial.println("RPM_SETTING_NOTICE invalid_record_retained_using_three_turn_default");
  const uint8_t sleepMinutes=prefs.getUChar("sleep_min",InactivityTimer::DEFAULT_MINUTES);
  if(!inactivity.setMinutes(sleepMinutes))Serial.println("SLEEP_SETTING_NOTICE invalid_saved_value_using_3_min");
  const uint8_t savedBrightness=prefs.getUChar("bright_pct",40);
  if(savedBrightness>=10 && savedBrightness<=100 && savedBrightness%10==0)brightnessPercent=savedBrightness;
  else Serial.println("BRIGHTNESS_SETTING_NOTICE invalid_saved_value_using_40_pct");
  uint8_t pin=prefs.getUChar("ao_pin",1);
  if(pin<1 || pin>10)pin=1;
  extPower=prefs.getBool("ext5v",false);
  saveError=!practiceStore.begin(practice);
  practice.newSession(); // Boot starts a fresh metric/session boundary; old scalar history stays intact.
  referenceError=!motionStore.begin(referenceMotion);
  if(const auto *last=practice.recent()) {
    latestMotion.number=last->number;latestMotion.rpm=last->rpm;
    if(referenceMotion.valid() && referenceMotion.fused && referenceMotion.number==last->number)latestMotion=referenceMotion;
  }
  M5.Power.setExtOutput(extPower);
  M5.Display.setRotation(DISPLAY_ROTATION);M5.Display.setBrightness(backlightValue());M5.Display.setTextSize(1);
  screen.setColorDepth(16);screenReady=screen.createSprite(M5.Display.width(),M5.Display.height())!=nullptr;
  if(!screenReady)Serial.println("DISPLAY_NOTICE direct_draw_fallback");
  if(!M5.Imu.isEnabled())Serial.println("LEVEL_NOTICE imu_unavailable");
  if(saveError)Serial.println("HISTORY_ERROR storage unavailable; existing bytes retained");
  M5.BtnA.setHoldThresh(1000);M5.BtnB.setHoldThresh(1000);
  if(!acquisition.begin(pin,rpmEstimator))Serial.println("ADC_ERROR acquisition_task_allocation");
  if(!imuAcquisition.begin())Serial.println("MOTION_NOTICE IMU task unavailable; level uses UI fallback");
  pollBattery(millis(),acquisition.snapshot());
  powerRecord(wakingFromStandby?PowerDiagnostics::Wake:PowerDiagnostics::Boot,loggedWake);
  powerLogTick=lastPowerSample=millis();
  Serial.printf("POWER_WAKE esp_cause=%d pm1_flags_valid=%d pm1_flags=0x%02x pending_standby=%d\n",int(wakeCause),pm1WakeValid,pm1WakeFlags,wakingFromStandby);
  inactivity.touch(millis());
  Serial.printf("BOOT LaunchLab Mini %s ppr=1 min_rpm=1000 min_mark=80 edge_fraction=0.70 sample_hz=50000 task_core=0\n",VERSION);
  Serial.printf("RPM_SETTING_BOOT selected=%s default=three_turn_peak legacy_history=retained_metric_not_encoded\n",RpmEstimator::name(rpmEstimator));
  Serial.println("READY commands: p status, P saved power log, i shake-wake arm/readback/restore check, a recent/live, o hold A (main tournament toggle), d signal, h history, c next view, b older, n new session, u history export, e motion export (including retained reference), q labeled recap demo, t labeled history demo, y/z guarded history/reference storage check, v screen, w recorder export, x ext5V, g<N><newline> GPIO1..10, s display stress, j 200ms UI stall");
}

void loop() {
  if(imuAcquisition.lock()){M5.update();imuAcquisition.unlock();}
  pollLevel(millis());
  Snapshot s=acquisition.snapshot();
  if(M5.BtnA.isPressed() || M5.BtnB.isPressed() || M5.BtnA.wasReleased() || M5.BtnB.wasReleased())
    inactivity.touch(millis());
  if(M5.BtnA.wasHold())holdA();
  if(M5.BtnA.wasClicked() && !tournamentMode) {
    if(historyPage && !diagnostics)nextView();
    else toggleFeedback();
  }
  if(M5.BtnB.wasHold())browseOlder();
  if(M5.BtnB.wasClicked())toggleHistory();
  static char command[8]={};static uint8_t used=0;
  // Bound incoming work; an unending USB stream cannot starve button/draw work.
  for(unsigned n=0;n<32 && Serial.available();++n) {
    const char c=Serial.read();
    // Status polling is observational; other explicit USB actions count as use.
    if(c!='p' && c!='P' && c!='\n' && c!='\r')inactivity.touch(millis());
    if(used || c=='g') {
      if(c=='\n' || c=='\r') {
        char *end=nullptr;const long pin=strtol(command+1,&end,10);
        if(end!=command+1 && *end==0 && pin>=1 && pin<=10) {
          if(acquisition.request(Action::Pin,uint8_t(pin)))prefs.putUChar("ao_pin",pin);
          else Serial.println("COMMAND_ERROR gpio_init");
          dirty=true;
        } else Serial.println("COMMAND_ERROR gpio_must_be_1_to_10");
        used=0;command[0]=0;
      } else if(used<sizeof(command)-1){command[used++]=c;command[used]=0;}
      else {used=0;command[0]=0;Serial.println("COMMAND_ERROR too_long");}
    } else if(c=='p')status();
    else if(c=='P')exportPowerLog();
    else if(c=='S'){
      inactivity.touch(millis()-inactivity.timeout());
      Serial.println("POWER_SLEEP_TEST requested=1 normal_save_and_sleep_path=1");
    }
    else if(c=='i') {
      if(acquisition.request(Action::IdleCheckpointBegin,s.launches)) {
        if(imuAcquisition.lock()) {
          const bool armed=shakeWake.arm(),restored=shakeWake.restore();
          M5.Power.setExtOutput(extPower);imuAcquisition.unlock();
          Serial.printf("SHAKE_WAKE_CHECK armed=%d restored=%d sleep=0\n",armed,restored);
        }
        acquisition.request(Action::CheckpointEnd);
      }
    }
    else if(c=='a')toggleFeedback();
    else if(c=='o')holdA();
    else if(c=='d'){diagnostics=!diagnostics;dirty=true;}
    else if(c=='h')toggleHistory();
    else if(c=='c')nextView();
    else if(c=='e')exportMotion();
    else if(c=='q') {
      historyPage=diagnostics=false;motionDemo=true;
      MotionUI::makeDemo(demoMotion,false);
      launchFeedback.show(millis());dirty=true;
      Serial.println("RECAP_DEMO synthetic only; real launches and reference unchanged");
    }
    else if(c=='b')browseOlder();
    else if(c=='n')newSession();
    else if(c=='u')exportHistory();
    else if(c=='t')previewHistory();
    else if(c=='y')checkStorage();
    else if(c=='z')checkMotionStorage();
    else if(c=='v')exportScreen();
    else if(c=='w')exportSignal();
    else if(c=='x') {
      // Explicit command only. No automatic voltage/power changes in sampling.
      if(!imuAcquisition.lock()){Serial.println("COMMAND_ERROR power_busy");continue;}
      extPower=!extPower;M5.Power.setExtOutput(extPower);imuAcquisition.unlock();prefs.putBool("ext5v",extPower);
      acquisition.request(Action::Reset);dirty=true;status();
    } else if(c=='s'){stress=!stress;diagnostics=true;dirty=true;}
    else if(c=='j'){++uiStalls;delay(200);}
  }
  Snapshot event;
  while(acquisition.takeEvent(event)) {
    if(event.revision!=lastRevision) {
      lastRevision=event.revision;
      Serial.printf("LAUNCH_RESULT valid=%d peak_rpm=%.1f revs=%lu amplitude=%.1f start_noise=%.1f launches=%lu end=%s t_us=%llu\n",
        event.valid,event.resultRpm,(unsigned long)event.revolutions,event.amplitude,event.startNoise,
        (unsigned long)event.launches,event.endName(),(unsigned long long)event.detectorUs);
      if(practice.accept(event.launches,event.valid,event.resultRpm,millis())) {
        prepareMotion(event);logLaunchMetrics(event);
        inactivity.touch(millis());
        Serial.printf("HISTORY_ADDED number=%lu session=%lu rpm=%.1f\n",(unsigned long)practice.recent()->number,
          (unsigned long)practice.recent()->session,practice.recent()->rpm);historyOffset=0;
      }
      dirty=true;
    }
    if(event.phase!=lastPhase || event.signalFault!=lastFault) {
      lastPhase=event.phase;lastFault=event.signalFault;dirty=true;
      Serial.printf("RPM_STATE state=%s t_us=%llu contrast=%.1f noise=%.1f\n",event.stateName(),
        (unsigned long long)event.detectorUs,event.contrast,event.noise);
    }
  }
  s=acquisition.snapshot();
  const uint32_t now=millis();
  if(launchFeedback.tick(now)){dirty=true;motionDemo=false;Serial.printf("MAIN_FEEDBACK shown=0 reason=timeout t_ms=%lu\n",(unsigned long)now);}
  if(s.phase==AnalogTachometer::Phase::Launch)inactivity.touch(now);
  finishMotion();
  saveHistory(now,s);s=acquisition.snapshot();
  pollBattery(now,s);
  tickPowerLog(now,s);
  pollUsbAwake(now,s);
  autoPowerOff(now,s);
  if(newSessionAt && now-newSessionAt>=1500){newSessionAt=0;dirty=true;}
  if(stress && now-lastDraw>=50)dirty=true;
  if(diagnostics && now-lastDraw>=500)dirty=true;
  if(historyPage && historyView==PracticeUI::View::Battery && now-lastDraw>=1000)dirty=true;
  if(!tournamentMode && !diagnostics && !historyPage && launchFeedback.shown() && !motionPending &&
     MotionReplay::playbackNeedsFrame(motionDemo?demoMotion:latestMotion,launchFeedback.replayElapsed(now),launchFeedback.lastReplayElapsed()) && now-lastDraw>=50)dirty=true;
  if(!tournamentMode && !diagnostics && !historyPage && !launchFeedback.shown() && now-lastDraw>=100) {
    const auto tilt=level.reading(now);
    if(tilt.state!=drawnLevel.state || (tilt.valid() &&
      (std::fabs(tilt.degrees-drawnLevel.degrees)>=0.15f ||
       std::fabs(tilt.right-drawnLevel.right)>=0.02f || std::fabs(tilt.down-drawnLevel.down)>=0.02f)))dirty=true;
  }
  // Avoid electrical display changes through an ordinary measured burst.
  // Stress mode intentionally exercises the screen even during a burst.
  if(dirty && (stress || s.phase!=AnalogTachometer::Phase::Launch)) {
    draw(s);lastDraw=millis();dirty=false;
  }
  if(Serial && now-lastStatus>=2000){lastStatus=now;status();}
  delay(1);
}

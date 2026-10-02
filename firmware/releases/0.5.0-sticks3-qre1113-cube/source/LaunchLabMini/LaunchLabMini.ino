#include <M5Unified.h>
#include <Preferences.h>
#include <memory>
#include "acquisition.h"
#include "level_indicator.h"
#include "practice_store.h"
#include "practice_ui.h"
#include "power_status.h"
#include "motion_acquisition.h"
#include "motion_store.h"
#include "motion_ui.h"
#include "launch_feedback.h"

static constexpr char VERSION[] = "0.5.0-sticks3-cube";
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
static unsigned historyOffset=0;
static uint32_t lastSaveTry=0,saveCount=0,saveErrors=0,maxSaveUs=0,newSessionAt=0;
static bool screenReady=false;
static bool diagnostics=false,extPower=false,stress=false,dirty=true;
static uint32_t lastDraw=0,lastStatus=0,lastRevision=0,maxDrawUs=0,uiStalls=0;
static uint32_t lastImuPoll=0,maxImuPollUs=0;
static StickS3Level::Reading drawnLevel;
static InactivityTimer inactivity;
static StickS3Battery battery;
static uint32_t lastBatteryPoll=0,maxBatteryPollUs=0,lastShutdownTry=0;
static bool batteryPolled=false;
static StickS3MotionAcquisition imuAcquisition;
static MotionStore motionStore;
static LaunchMotion::Trace latestMotion,referenceMotion,demoMotion,demoReference;
static bool motionPending=false,referencePending=false,referenceError=false,recreateArmed=false,motionDemo=false;
static uint64_t motionStart=0,motionEnd=0,lastLevelSampleUs=0;
static uint32_t motionDrops=0;
static LaunchFeedback launchFeedback;
static AnalogTachometer::Phase lastPhase=AnalogTachometer::Phase::Paused;
static bool lastFault=false;
using Action=StickS3Acquisition::Action;
using Snapshot=StickS3Acquisition::Snapshot;

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
  Serial.printf("HISTORY_STATUS records=%u sessions=%u session=%lu session_pulls=%lu session_avg=%.1f generation=%lu pending=%d store_ready=%d save_errors=%lu saves=%lu max_save_us=%lu page=%s view=%u offset=%u demo=%d ui_stack_free=%lu\n",
    practice.size(),practice.sessions(),session?(unsigned long)session->number:0ul,
    session?(unsigned long)session->count:0ul,session?session->mean():0,
    (unsigned long)practice.generation(),practiceStore.pending(practice),practiceStore.ready(),
    (unsigned long)saveErrors,(unsigned long)saveCount,(unsigned long)maxSaveUs,
    diagnostics?"signal":historyPage?"history":"live",unsigned(historyView),historyOffset,demo,
    (unsigned long)uxTaskGetStackHighWaterMark(nullptr));
  const uint32_t now=millis();
  Serial.printf("POWER_STATUS auto_off_s=600 idle_s=%lu off_in_s=%lu battery_valid=%d battery_mv=%u battery_pct=%d charging=%s max_battery_poll_us=%lu\n",
    (unsigned long)(inactivity.elapsed(now)/1000),(unsigned long)((inactivity.remaining(now)+999)/1000),
    battery.valid(now),unsigned(battery.millivolts),battery.valid(now)?battery.percent:-1,
    battery.chargeName(),(unsigned long)maxBatteryPollUs);
  const auto imu=imuAcquisition.snapshot();
  Serial.printf("MOTION_STATUS imu_core=0 imu_task=%d paired_samples=%lu accel_samples=%lu max_gap_us=%lu gaps=%lu max_poll_us=%lu stack_free=%lu gate_misses=%lu latest=%lu quality=%s pending=%d ref=%lu ref_rpm=%.1f ref_pending=%d ref_store_ready=%d ref_save_error=%d armed=%d dropped=%lu demo=%d feedback=%d\n",
    imuAcquisition.running(),(unsigned long)imu.pairedSamples,(unsigned long)imu.accelSamples,
    (unsigned long)imu.maxGapUs,(unsigned long)imu.gaps,(unsigned long)imu.maxPollUs,(unsigned long)imu.stackFree,(unsigned long)imu.gateMisses,
    (unsigned long)latestMotion.number,LaunchMotion::name(latestMotion.quality),motionPending,
    (unsigned long)referenceMotion.number,referenceMotion.rpm,referencePending,motionStore.ready(),referenceError,
    recreateArmed,(unsigned long)motionDrops,motionDemo,launchFeedback.shown());
}

static void pollBattery(uint32_t now,const Snapshot &s) {
  if(s.phase==AnalogTachometer::Phase::Launch || (batteryPolled && now-lastBatteryPoll<5000))return;
  if(!imuAcquisition.lock())return;
  batteryPolled=true;lastBatteryPoll=now;
  const int64_t started=esp_timer_get_time();
  uint16_t mv=0;uint8_t bits=0;
  const bool voltageRead=M5.Power.M5pm1.getBatteryVoltage(&mv);
  const bool chargeRead=M5.Power.M5pm1.getGPIOInputBits(&bits);
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
  g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString("Approx. charge",cx,77,1);
  g.drawRoundRect(29,96,74,25,3,TFT_DARKGREY);g.fillRect(103,103,4,11,TFT_DARKGREY);
  if(valid)g.fillRect(33,100,66*battery.percent/100,17,battery.percent<=20?TFT_ORANGE:TFT_CYAN);
  g.setTextColor(TFT_WHITE,TFT_BLACK);
  if(valid)snprintf(line,sizeof(line),"%.2f V",battery.millivolts/1000.0);else snprintf(line,sizeof(line),"Reading unavailable");
  g.drawString(line,cx,133,2);
  g.drawString(!battery.chargeKnown?"Charge status unknown":battery.charging?"Charging":"Not charging",cx,161,1);
  const uint32_t seconds=(inactivity.remaining(now)+999)/1000;
  snprintf(line,sizeof(line),"Off in %lu:%02lu",(unsigned long)(seconds/60),(unsigned long)(seconds%60));
  g.drawString(line,cx,184,2);
  g.setTextColor(TFT_DARKGREY,TFT_BLACK);g.drawString("10 min without use",cx,208,1);
  g.drawString("A view  B back",cx,231,1);
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

static void draw(const Snapshot &s) {
  const int64_t started=esp_timer_get_time();
  auto &view=screenReady?static_cast<lgfx::LGFXBase &>(screen):static_cast<lgfx::LGFXBase &>(M5.Display);
  if(!screenReady){acquisition.displayBoundary(true);M5.Display.startWrite();}
  view.fillScreen(TFT_BLACK);
  const int cx=view.width()/2;
  view.setTextDatum(top_center);
  view.setTextColor(TFT_WHITE,TFT_BLACK);
  view.drawString(newSessionAt && millis()-newSessionAt<1500?"New session ready":"LaunchLab Mini",cx,8,2);
  view.setTextColor(s.ready && !s.signalFault?TFT_GREEN:TFT_ORANGE,TFT_BLACK);
  view.drawString(s.stateName(),cx,32,2);
  view.setTextColor(TFT_WHITE,TFT_BLACK);
  if(diagnostics) {
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
    if(historyView==PracticeUI::View::Battery)drawBattery(view,millis());
    else if(historyView==PracticeUI::View::Motion || historyView==PracticeUI::View::Recreate)
      MotionUI::draw(view,motionDemo?demoMotion:latestMotion,motionDemo?demoReference:referenceMotion,
        historyView==PracticeUI::View::Recreate,motionPending,recreateArmed,referenceError,motionDemo);
    else PracticeUI::draw(view,demo?demoPractice:practice,historyView,historyOffset,demo,saveError,practiceStore.pending(practice));
  } else if(launchFeedback.shown()) {
    view.fillScreen(TFT_BLACK);
    MotionUI::feedback(view,motionDemo?demoMotion:latestMotion,motionDemo?demoReference:referenceMotion,
      motionPending && !motionDemo,motionDemo,std::min(1.0f,launchFeedback.elapsed(millis())/1400.0f));
  } else {
    char rpm[16];
    if(s.valid)snprintf(rpm,sizeof(rpm),"%.0f",s.resultRpm);
    else snprintf(rpm,sizeof(rpm),"--");
    view.setTextDatum(top_center);
    // Keep large values inside the narrow portrait width as well.
    const int rpmFont=view.textWidth(rpm,&fonts::Font6)<=view.width()-8?6:4;
    view.drawString(rpm,cx,53,rpmFont);
    view.drawString("RPM",cx,100,2);
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
  if(diagnostics || (!historyPage && !launchFeedback.shown())) {
    view.setTextDatum(top_center);view.setTextColor(TFT_DARKGREY,TFT_BLACK);
    view.drawString("A recent  B history",cx,231,1);
  }
  if(screenReady){acquisition.displayBoundary(true);M5.Display.startWrite();screen.pushSprite(0,0);}
  M5.Display.endWrite();
  acquisition.displayBoundary(false);
  maxDrawUs=std::max(maxDrawUs,uint32_t(esp_timer_get_time()-started));
}

static void pollLevel(uint32_t now) {
  if(imuAcquisition.running()) {
    const auto sample=imuAcquisition.snapshot();
    if(sample.accelUs && sample.accelUs!=lastLevelSampleUs) {
      lastLevelSampleUs=sample.accelUs;level.feed(sample.a[0],sample.a[1],sample.a[2],uint32_t(sample.accelUs/1000));
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
  historyPage=diagnostics=motionDemo=demo=false;
  launchFeedback.toggle(millis(),latestMotion.number!=0);dirty=true;
  Serial.printf("MAIN_FEEDBACK shown=%d reason=button t_ms=%lu\n",launchFeedback.shown(),(unsigned long)millis());
}

static void toggleHistory() {
  launchFeedback.clear();
  if(demo){demo=false;historyPage=false;}else historyPage=!historyPage;
  motionDemo=false;diagnostics=false;historyOffset=0;dirty=true;
  if(historyPage && historyView==PracticeUI::View::Recreate && !referenceMotion.valid())recreateArmed=true;
}
static bool motionPage(){return historyPage && !diagnostics && (historyView==PracticeUI::View::Motion || historyView==PracticeUI::View::Recreate);}
static void nextView() {
  historyView=PracticeUI::next(historyView);historyOffset=0;dirty=true;
  if(historyView==PracticeUI::View::Recreate && !referenceMotion.valid())recreateArmed=true;
}
static void selectReference() {
  if(motionDemo){motionDemo=false;dirty=true;return;}
  if(latestMotion.valid() && !motionPending) {
    referenceMotion=latestMotion;referencePending=true;referenceError=false;recreateArmed=false;
    Serial.printf("MOTION_REFERENCE selected=%lu rpm=%.1f\n",(unsigned long)referenceMotion.number,referenceMotion.rpm);
  } else {recreateArmed=true;Serial.println("MOTION_REFERENCE next usable pull will be reference");}
  dirty=true;
}
static void prepareMotion(const Snapshot &event) {
  if(motionPending)++motionDrops;
  latestMotion={};latestMotion.number=practice.recent()->number;latestMotion.rpm=event.resultRpm;
  motionStart=event.burstStartHostUs;motionEnd=event.burstEndHostUs;motionPending=true;
  historyPage=diagnostics=motionDemo=demo=false;launchFeedback.show(millis());dirty=true;
}
static void finishMotion() {
  if(!motionPending)return;
  const uint64_t now=esp_timer_get_time();const auto imu=imuAcquisition.snapshot();
  if(now<motionEnd+250000 || (imu.pairedUs<motionEnd+250000 && now<motionEnd+1000000))return;
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
  if(recreateArmed && latestMotion.valid())selectReference();
}
static void exportMotion() {
  for(const auto *t:{&referenceMotion,&latestMotion}) {
    const char *role=t==&referenceMotion?"reference":"latest";
    Serial.printf("MOTION_EXPORT role=%s number=%lu rpm=%.3f quality=%s count=%u duration_ms=%lu stationary_bias=%d\n",role,
      (unsigned long)t->number,t->rpm,LaunchMotion::name(t->quality),t->count,(unsigned long)t->durationMs,t->stationaryBias);
    if(t->valid())for(unsigned i=0;i<t->count;++i) {
      const auto &p=t->points[i];Serial.printf("MOTION_POINT role=%s t_ms=%d accel_change_g=%.3f,%.3f,%.3f gyro_dps=%.1f,%.1f,%.1f q=%.5f,%.5f,%.5f,%.5f\n",
        role,p.ms,p.a[0]*.001f,p.a[1]*.001f,p.a[2]*.001f,p.g[0]*.1f,p.g[1]*.1f,p.g[2]*.1f,
        p.q[0]/16384.0f,p.q[1]/16384.0f,p.q[2]/16384.0f,p.q[3]/16384.0f);
    }
    auto replay=std::unique_ptr<MotionReplay::Replay>(new(std::nothrow) MotionReplay::Replay);
    if(replay && replay->build(*t)) {
      MotionReplay::Cube cube;cube.fit(*replay);
      Serial.printf("REPLAY_EXPORT role=%s number=%lu estimated=1 initial_velocity=assumed_zero count=%u cube_side_m=%.5f\n",
        role,(unsigned long)t->number,MotionReplay::Replay::COUNT,cube.high.x-cube.low.x);
      for(unsigned i=0;i<MotionReplay::Replay::COUNT;++i) {
        const auto &p=replay->center[i];Serial.printf("REPLAY_POINT role=%s t_ms=%lu estimate_m=%.5f,%.5f,%.5f\n",role,
          (unsigned long)(t->durationMs*i/(MotionReplay::Replay::COUNT-1)),p.x,p.y,p.z);
      }
    }
  }
}
static void newSession() {
  practice.newSession();newSessionAt=millis();demo=false;diagnostics=false;historyPage=false;dirty=true;
  Serial.println("HISTORY_SESSION next accepted launch starts a new session");
}
static void browseOlder() {
  if(!historyPage){diagnostics=!diagnostics;dirty=true;return;}
  if(motionPage()){recreateArmed=true;motionDemo=false;dirty=true;return;}
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
  const bool reference=referencePending && motionStore.ready();
  if(motionPending || (!history && !reference) || now-lastSaveTry<1000 || s.phase==AnalogTachometer::Phase::Launch)return;
  if(!reference && s.phase!=AnalogTachometer::Phase::Hold && s.phase!=AnalogTachometer::Phase::Paused)return;
  lastSaveTry=now;
  if(!acquisition.request(reference?Action::IdleCheckpointBegin:Action::CheckpointBegin,s.launches))return;
  const int64_t started=esp_timer_get_time();
  const bool saved=!history || practiceStore.save(practice);
  if(reference) {
    const bool ok=motionStore.save(referenceMotion);referenceError=!ok;if(ok)referencePending=false;
    Serial.printf("MOTION_REF_SAVE ok=%d number=%lu bytes=%u\n",ok,(unsigned long)referenceMotion.number,unsigned(LaunchMotion::IMAGE_BYTES));
  }
  maxSaveUs=std::max(maxSaveUs,uint32_t(esp_timer_get_time()-started));
  if(saved){++saveCount;saveError=false;}else {++saveErrors;saveError=true;}
  if(!acquisition.request(Action::CheckpointEnd))Serial.println("HISTORY_ERROR ADC checkpoint resume failed");
  Serial.printf("HISTORY_SAVE ok=%d generation=%lu duration_us=%lu\n",saved,
    (unsigned long)practice.generation(),(unsigned long)(esp_timer_get_time()-started));
  dirty=true;
}

static void autoPowerOff(uint32_t now,const Snapshot &s) {
  if(!inactivity.due(now,s.phase==AnalogTachometer::Phase::Launch) ||
     (lastShutdownTry && now-lastShutdownTry<60000))return;
  lastShutdownTry=now;
  if(!acquisition.request(Action::ShutdownBegin,s.launches))return;
  // Finish any queued accepted result before saving; the owner is now stopped.
  Snapshot event;
  bool newPull=false;
  while(acquisition.takeEvent(event))if(practice.accept(event.launches,event.valid,event.resultRpm,now)){prepareMotion(event);newPull=true;}
  if(newPull) {
    inactivity.touch(now);lastShutdownTry=0;dirty=true;
    if(!acquisition.request(Action::CheckpointEnd))acquisition.request(Action::Pin,s.pin);
    return;
  }
  if(practiceStore.pending(practice) && (!practiceStore.ready() || !practiceStore.save(practice))) {
    saveError=true;++saveErrors;dirty=true;
    Serial.println("POWER_OFF_DEFERRED history_save_failed; retry in 60s");
    if(!acquisition.request(Action::CheckpointEnd))acquisition.request(Action::Pin,s.pin);
    return;
  }
  if(referencePending && (!motionStore.ready() || !motionStore.save(referenceMotion))) {
    referenceError=true;dirty=true;
    Serial.println("POWER_OFF_DEFERRED reference_save_failed");
    if(!acquisition.request(Action::CheckpointEnd))acquisition.request(Action::Pin,s.pin);return;
  }
  Serial.printf("POWER_OFF reason=inactivity idle_ms=%lu records=%u saved=1\n",
    (unsigned long)inactivity.elapsed(now),practice.size());
  Serial.flush();
  // Native StickS3 PM1 shutdown cuts power; M5Unified also sleeps the display
  // and enters deep sleep if external power keeps the ESP32 supplied.
  if(imuAcquisition.lock()){M5.Power.powerOff();imuAcquisition.unlock();}
  // A failed bus lock or a returned shutdown must never leave acquisition stopped.
  Serial.println("POWER_OFF_DEFERRED shutdown_returned_or_bus_busy");
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
  Serial.begin(115200);
  Serial.setTxTimeoutMs(10);
  auto cfg=M5.config();
  cfg.fallback_board=m5::board_t::board_M5StickS3;
  cfg.internal_mic=cfg.internal_spk=cfg.internal_rtc=false;cfg.internal_imu=true;
  cfg.external_imu=cfg.external_rtc=false;cfg.output_power=false;
  M5.begin(cfg);
  M5.Ex_I2C.release();
  prefs.begin("launchlab-mini",false);
  uint8_t pin=prefs.getUChar("ao_pin",1);
  if(pin<1 || pin>10)pin=1;
  extPower=prefs.getBool("ext5v",false);
  saveError=!practiceStore.begin(practice);
  referenceError=!motionStore.begin(referenceMotion);
  if(const auto *last=practice.recent()) {
    latestMotion.number=last->number;latestMotion.rpm=last->rpm;
    if(referenceMotion.valid() && referenceMotion.number==last->number)latestMotion=referenceMotion;
  }
  M5.Power.setExtOutput(extPower);
  M5.Display.setRotation(DISPLAY_ROTATION);M5.Display.setBrightness(100);M5.Display.setTextSize(1);
  screen.setColorDepth(16);screenReady=screen.createSprite(M5.Display.width(),M5.Display.height())!=nullptr;
  if(!screenReady)Serial.println("DISPLAY_NOTICE direct_draw_fallback");
  if(!M5.Imu.isEnabled())Serial.println("LEVEL_NOTICE imu_unavailable");
  if(saveError)Serial.println("HISTORY_ERROR storage unavailable; existing bytes retained");
  M5.BtnA.setHoldThresh(1000);M5.BtnB.setHoldThresh(1000);
  if(!acquisition.begin(pin))Serial.println("ADC_ERROR acquisition_task_allocation");
  if(!imuAcquisition.begin())Serial.println("MOTION_NOTICE IMU task unavailable; level uses UI fallback");
  inactivity.touch(millis());
  Serial.printf("BOOT LaunchLab Mini %s ppr=1 min_rpm=1000 min_mark=80 edge_fraction=0.70 sample_hz=50000 task_core=0\n",VERSION);
  Serial.println("READY commands: p status, a recent/live, d signal, h history, c next view, b older, n new session, u history export, m motion, r recreate, k use current reference, l next reference, e motion export, f labeled motion demo, q labeled recap demo, t labeled history demo, y/z guarded history/reference storage check, v screen, w recorder export, x ext5V, g<N><newline> GPIO1..10, s display stress, j 200ms UI stall");
}

void loop() {
  if(imuAcquisition.lock()){M5.update();imuAcquisition.unlock();}
  pollLevel(millis());
  Snapshot s=acquisition.snapshot();
  if(M5.BtnA.isPressed() || M5.BtnB.isPressed() || M5.BtnA.wasReleased() || M5.BtnB.wasReleased())
    inactivity.touch(millis());
  if(M5.BtnA.wasHold()){if(motionPage())selectReference();else newSession();}
  if(M5.BtnA.wasClicked()) {
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
    if(c!='p' && c!='\n' && c!='\r')inactivity.touch(millis());
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
    else if(c=='a')toggleFeedback();
    else if(c=='d'){diagnostics=!diagnostics;dirty=true;}
    else if(c=='h')toggleHistory();
    else if(c=='c')nextView();
    else if(c=='m' || c=='r') {
      historyPage=true;diagnostics=false;motionDemo=false;
      historyView=c=='m'?PracticeUI::View::Motion:PracticeUI::View::Recreate;
      if(c=='r' && !referenceMotion.valid())recreateArmed=true;dirty=true;
    }
    else if(c=='k')selectReference();
    else if(c=='l'){recreateArmed=true;motionDemo=false;dirty=true;}
    else if(c=='e')exportMotion();
    else if(c=='q') {
      historyPage=diagnostics=false;motionDemo=true;
      MotionUI::makeDemo(demoMotion,false);MotionUI::makeDemo(demoReference,true);
      launchFeedback.show(millis());dirty=true;
      Serial.println("RECAP_DEMO synthetic only; real launches and reference unchanged");
    }
    else if(c=='f') {
      motionDemo=!motionDemo;historyPage=true;historyView=PracticeUI::View::Recreate;diagnostics=false;
      MotionUI::makeDemo(demoMotion,false);MotionUI::makeDemo(demoReference,true);dirty=true;
      Serial.printf("MOTION_DEMO enabled=%d synthetic only; real reference unchanged\n",motionDemo);
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
        prepareMotion(event);
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
  autoPowerOff(now,s);
  if(newSessionAt && now-newSessionAt>=1500){newSessionAt=0;dirty=true;}
  if(stress && now-lastDraw>=50)dirty=true;
  if(diagnostics && now-lastDraw>=500)dirty=true;
  if(historyPage && historyView==PracticeUI::View::Battery && now-lastDraw>=1000)dirty=true;
  if(!diagnostics && !historyPage && launchFeedback.shown() && !motionPending &&
     (launchFeedback.elapsed(now)<1400 || launchFeedback.elapsed(lastDraw)<1400) && now-lastDraw>=50)dirty=true;
  if(!diagnostics && !historyPage && !launchFeedback.shown() && now-lastDraw>=100) {
    const auto tilt=level.reading(now);
    if(tilt.state!=drawnLevel.state || (tilt.valid() &&
      (std::fabs(tilt.degrees-drawnLevel.degrees)>=0.15f ||
       std::fabs(tilt.right-drawnLevel.right)>=0.02f || std::fabs(tilt.down-drawnLevel.down)>=0.02f)))dirty=true;
  }
  // Avoid electrical display changes through an ordinary measured burst.
  // Stress mode intentionally exercises the screen even during a burst.
  if(dirty && (stress || s.phase!=AnalogTachometer::Phase::Launch)) {
    draw(s);lastDraw=now;dirty=false;
  }
  if(Serial && now-lastStatus>=2000){lastStatus=now;status();}
  delay(1);
}

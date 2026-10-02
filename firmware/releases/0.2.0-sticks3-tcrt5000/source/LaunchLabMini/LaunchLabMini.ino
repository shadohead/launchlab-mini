#include <M5Unified.h>
#include <Preferences.h>
#include "acquisition.h"

static constexpr char VERSION[] = "0.2.0-sticks3-acquisition";
static constexpr uint32_t ANALOG_SAMPLE_HZ = StickS3Acquisition::SAMPLE_HZ;
#include "raw_transfer.h"
static StickS3Acquisition acquisition;
static Preferences prefs;
static bool diagnostics=false,extPower=false,stress=false,dirty=true;
static uint32_t lastDraw=0,lastStatus=0,lastRevision=0,maxDrawUs=0,uiStalls=0;
static AnalogTachometer::Phase lastPhase=AnalogTachometer::Phase::Paused;
static bool lastFault=false;
using Action=StickS3Acquisition::Action;
using Snapshot=StickS3Acquisition::Snapshot;

static void status() {
  const Snapshot s=acquisition.snapshot();
  Serial.printf("STATUS v=%s board=StickS3 board_id=%d gpio=%u adc_ready=%d suspended=%d ext5v=%d width=%d height=%d samples=%llu delivered_sps=%.0f mean=%.1f min=%lu max=%lu last=%lu overflow_events=%lu read_errors=%lu adc_error=%s\n",
    VERSION,int(M5.getBoard()),s.pin,s.ready,s.suspended,extPower,M5.Display.width(),M5.Display.height(),
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
  acquisition.displayBoundary(true);
  // One display transaction per frame; the independent sampler remains live.
  M5.Display.startWrite();
  M5.Display.fillScreen(TFT_BLACK);
  M5.Display.setTextDatum(top_left);
  M5.Display.setTextColor(TFT_WHITE,TFT_BLACK);
  M5.Display.drawString("LaunchLab Mini",8,5,2);
  M5.Display.setTextColor(s.ready && !s.signalFault?TFT_GREEN:TFT_ORANGE,TFT_BLACK);
  M5.Display.drawString(s.stateName(),8,29,2);
  M5.Display.setTextColor(TFT_WHITE,TFT_BLACK);
  if(diagnostics) {
    char line[64];
    snprintf(line,sizeof(line),"AO G%u: %lu",s.pin,(unsigned long)s.last);
    M5.Display.drawString(line,8,54,2);
    snprintf(line,sizeof(line),"Range %lu-%lu",(unsigned long)s.minimum,(unsigned long)s.maximum);
    M5.Display.drawString(line,8,76,2);
    snprintf(line,sizeof(line),"%.0f samples/s",s.rate);
    M5.Display.drawString(line,8,98,2);
  } else {
    char rpm[16];
    if(s.valid)snprintf(rpm,sizeof(rpm),"%.0f",s.resultRpm);
    else snprintf(rpm,sizeof(rpm),"--");
    M5.Display.setTextDatum(top_center);
    M5.Display.drawString(rpm,120,53,6);
    M5.Display.drawString("RPM",120,104,2);
  }
  M5.Display.setTextDatum(top_left);
  M5.Display.setTextColor(TFT_DARKGREY,TFT_BLACK);
  M5.Display.drawString("A pause   B signal",8,121,1);
  M5.Display.endWrite();
  acquisition.displayBoundary(false);
  maxDrawUs=std::max(maxDrawUs,uint32_t(esp_timer_get_time()-started));
}

static void enable(bool enabled) {
  if(!acquisition.request(Action::Enabled,enabled))Serial.println("COMMAND_ERROR enable_timeout");
  dirty=true;
}

void setup() {
  Serial.begin(115200);
  Serial.setTxTimeoutMs(10);
  auto cfg=M5.config();
  cfg.fallback_board=m5::board_t::board_M5StickS3;
  cfg.internal_mic=cfg.internal_spk=cfg.internal_imu=cfg.internal_rtc=false;
  cfg.external_imu=cfg.external_rtc=false;cfg.output_power=false;
  M5.begin(cfg);
  M5.Ex_I2C.release();
  prefs.begin("launchlab-mini",false);
  uint8_t pin=prefs.getUChar("ao_pin",1);
  if(pin<1 || pin>10)pin=1;
  extPower=prefs.getBool("ext5v",false);
  M5.Power.setExtOutput(extPower);
  M5.Display.setRotation(1);M5.Display.setBrightness(100);M5.Display.setTextSize(1);
  if(!acquisition.begin(pin))Serial.println("ADC_ERROR acquisition_task_allocation");
  Serial.printf("BOOT LaunchLab Mini %s ppr=1 min_rpm=1000 min_mark=80 edge_fraction=0.70 sample_hz=50000 task_core=0\n",VERSION);
  Serial.println("READY commands: p status, a pause/resume, d signal, w recorder export, x ext5V, g<N><newline> GPIO1..10, s display stress, j 200ms UI stall");
}

void loop() {
  M5.update();
  Snapshot s=acquisition.snapshot();
  if(M5.BtnA.wasPressed())enable(!s.enabled);
  if(M5.BtnB.wasPressed()){diagnostics=!diagnostics;dirty=true;}
  static char command[8]={};static uint8_t used=0;
  // Bound incoming work; an unending USB stream cannot starve button/draw work.
  for(unsigned n=0;n<32 && Serial.available();++n) {
    const char c=Serial.read();
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
    else if(c=='a')enable(!acquisition.snapshot().enabled);
    else if(c=='d'){diagnostics=!diagnostics;dirty=true;}
    else if(c=='w')exportSignal();
    else if(c=='x') {
      // Explicit command only. No automatic voltage/power changes in sampling.
      extPower=!extPower;M5.Power.setExtOutput(extPower);prefs.putBool("ext5v",extPower);
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
  if(stress && now-lastDraw>=50)dirty=true;
  if(diagnostics && now-lastDraw>=500)dirty=true;
  // Avoid electrical display changes through an ordinary measured burst.
  // Stress mode intentionally exercises the screen even during a burst.
  if(dirty && (stress || s.phase!=AnalogTachometer::Phase::Launch)) {
    draw(s);lastDraw=now;dirty=false;
  }
  if(Serial && now-lastStatus>=2000){lastStatus=now;status();}
  delay(1);
}

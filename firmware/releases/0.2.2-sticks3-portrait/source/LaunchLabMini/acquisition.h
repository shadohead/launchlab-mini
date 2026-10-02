#pragma once
#include "esp_adc/adc_continuous.h"
#include "esp_timer.h"
#include "driver/gpio.h"
#include "soc/soc_caps.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "sensor_profile.h"
#include "sample_ring.h"

// All ADC API calls, detector state and recorder writes have ONE owner on core
// 0. M5Unified, drawing, USB and Preferences stay on the Arduino/UI core. No
// sample-by-sample logging, cross-core detector reads, or ADC calls from UI.
class StickS3Acquisition {
public:
  static constexpr uint32_t SAMPLE_HZ=AnalogTachometer::SAMPLE_HZ;
  static constexpr uint32_t RING_SAMPLES=SAMPLE_HZ*60;
  enum class Action:uint8_t { Enabled, Pin, Suspend, Resume, Reset };
  struct Snapshot {
    AnalogTachometer::Phase phase=AnalogTachometer::Phase::Settling;
    AnalogTachometer::End ended=AnalogTachometer::End::None;
    bool ready=false,suspended=false,enabled=true,valid=false,signalFault=false;
    uint8_t pin=1;
    esp_err_t error=ESP_OK;
    uint64_t samples=0,detectorUs=0,ringFirst=0;
    uint32_t ringCount=0,revision=0,launches=0,revolutions=0,edges=0;
    uint32_t weak=0,slow=0,shape=0,inconsistent=0,rearmExtensions=0,rearmMs=0;
    uint32_t last=0,minimum=0,maximum=0,overflows=0,readErrors=0,invalidFrames=0;
    uint32_t lostEvents=0,maxBatchUs=0,maxReadGapUs=0,stackFree=0;
    float mean=0,rate=0,processingPercent=0,resultRpm=0,peakRpm=0;
    float candidateRpm=0,noise=0,amplitude=0,startNoise=0,contrast=0,hysteresis=0;
    const char *stateName() const {
      if(suspended)return "EXPORT";
      if(!ready)return "ADC ERROR";
      if(signalFault)return "CHECK SENSOR";
      switch(phase){case AnalogTachometer::Phase::Paused:return "PAUSED";
        case AnalogTachometer::Phase::Settling:return "STARTING";
        case AnalogTachometer::Phase::Ready:return "READY";
        case AnalogTachometer::Phase::Launch:return "MEASURING";default:return "REARM";}
    }
    const char *endName() const {
      switch(ended){case AnalogTachometer::End::Slowdown:return "slowdown";
        case AnalogTachometer::End::Gap:return "gap";
        case AnalogTachometer::End::Signal:return "signal_fault";
        case AnalogTachometer::End::DataLoss:return "data_loss";
        case AnalogTachometer::End::Cancel:return "cancelled";default:return "none";}
    }
  };
  bool begin(uint8_t pin) {
    pin_=pin;
    storage_=static_cast<uint16_t *>(heap_caps_malloc(RING_SAMPLES*sizeof(uint16_t),MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT));
    ring_=SampleRing(storage_,RING_SAMPLES);
    commands_=xQueueCreate(4,sizeof(Command));
    replies_=xQueueCreate(4,sizeof(Reply));
    events_=xQueueCreate(16,sizeof(Snapshot));
    if(!commands_ || !replies_ || !events_)return false;
    return xTaskCreatePinnedToCore(taskEntry,"optical",8192,this,3,&task_,0)==pdPASS;
  }
  bool request(Action action,uint8_t value=0) {
    if(!task_)return false;
    const Command command{action,value,++requestId_};
    if(xQueueSend(commands_,&command,pdMS_TO_TICKS(100))!=pdTRUE)return false;
    const TickType_t started=xTaskGetTickCount(),timeout=pdMS_TO_TICKS(2000);
    Reply reply{};
    while(xTaskGetTickCount()-started<timeout) {
      if(xQueueReceive(replies_,&reply,pdMS_TO_TICKS(20))==pdTRUE && reply.id==command.id)return reply.ok;
    }
    return false;
  }
  Snapshot snapshot() {
    portENTER_CRITICAL(&snapshotMux_);Snapshot copy=snapshot_;portEXIT_CRITICAL(&snapshotMux_);return copy;
  }
  bool takeEvent(Snapshot &event){return events_ && xQueueReceive(events_,&event,0)==pdTRUE;}
  const uint16_t *storage() const{return storage_;}
  // Recorder markers describe the first acquired batch consumed after each UI
  // boundary (about 5 ms resolution). They do not invoke the Waveshare's
  // empirically measured 2.5-14 ms electrical blanking on a different board.
  void displayBoundary(bool start) {
    portENTER_CRITICAL(&marksMux_);pendingMarks_|=start?0x8000:0x4000;portEXIT_CRITICAL(&marksMux_);
  }
private:
  struct Command {Action action;uint8_t value;uint32_t id;};
  struct Reply {uint32_t id;bool ok;};
  uint16_t *storage_=nullptr;
  SampleRing ring_{nullptr,0};
  AnalogTachometer detector_;
  adc_continuous_handle_t adc_=nullptr;
  QueueHandle_t commands_=nullptr,replies_=nullptr,events_=nullptr;
  TaskHandle_t task_=nullptr;
  portMUX_TYPE snapshotMux_=portMUX_INITIALIZER_UNLOCKED;
  portMUX_TYPE overflowMux_=portMUX_INITIALIZER_UNLOCKED;
  portMUX_TYPE marksMux_=portMUX_INITIALIZER_UNLOCKED;
  Snapshot snapshot_;
  uint32_t requestId_=0,overflows_=0,seenOverflows_=0,readErrors_=0,invalidFrames_=0,lostEvents_=0;
  uint16_t pendingMarks_=0;
  uint8_t pin_=1,channel_=0;
  bool ready_=false,suspended_=false;
  esp_err_t error_=ESP_OK;
  uint64_t samples_=0,sum_=0;
  uint32_t count_=0,minimum_=4095,maximum_=0,last_=0,maxBatchUs_=0,maxReadGapUs_=0;
  int64_t windowStart_=0,lastRead_=0,lastPublish_=0,retryAt_=0;
  uint64_t processingUs_=0;
  float mean_=0,rate_=0,processingPercent_=0;
  uint32_t displayMin_=0,displayMax_=0,previousRevision_=0;
  AnalogTachometer::Phase previousPhase_=AnalogTachometer::Phase::Paused;
  bool previousFault_=false;
  static void taskEntry(void *self){static_cast<StickS3Acquisition *>(self)->run();}
  static bool IRAM_ATTR overflow(adc_continuous_handle_t,const adc_continuous_evt_data_t *,void *self) {
    auto &owner=*static_cast<StickS3Acquisition *>(self);
    portENTER_CRITICAL_ISR(&owner.overflowMux_);++owner.overflows_;portEXIT_CRITICAL_ISR(&owner.overflowMux_);
    return false;
  }
  uint32_t overflowCount() {
    portENTER_CRITICAL(&overflowMux_);const uint32_t copy=overflows_;portEXIT_CRITICAL(&overflowMux_);return copy;
  }
  uint16_t takeMarks() {
    portENTER_CRITICAL(&marksMux_);const uint16_t copy=pendingMarks_;pendingMarks_=0;portEXIT_CRITICAL(&marksMux_);return copy;
  }
  void resetWindow() {
    count_=0;sum_=0;minimum_=4095;maximum_=0;processingUs_=0;
    windowStart_=esp_timer_get_time();lastRead_=0;
  }
  void discontinuity() {ring_.discontinuity();detector_.dataLoss();takeMarks();resetWindow();}
  void closeAdc() {
    if(adc_) {
      if(ready_)adc_continuous_stop(adc_);
      adc_continuous_deinit(adc_);adc_=nullptr;
    }
    ready_=false;
  }
  bool initAdc() {
    adc_unit_t unit;adc_channel_t channel;
    error_=adc_continuous_io_to_channel(pin_,&unit,&channel);
    if(error_!=ESP_OK || unit!=ADC_UNIT_1 || pin_<1 || pin_>10) {
      error_=ESP_ERR_INVALID_ARG;return false;
    }
    channel_=uint8_t(channel);
    gpio_set_direction(static_cast<gpio_num_t>(pin_),GPIO_MODE_INPUT);
    gpio_set_pull_mode(static_cast<gpio_num_t>(pin_),GPIO_FLOATING);
    adc_continuous_handle_cfg_t handle={};
    handle.max_store_buf_size=32768;handle.conv_frame_size=1024;
    error_=adc_continuous_new_handle(&handle,&adc_);
    adc_digi_pattern_config_t pattern={};
    pattern.atten=ADC_ATTEN_DB_12;pattern.channel=channel_;
    pattern.unit=ADC_UNIT_1;pattern.bit_width=12;
    adc_continuous_config_t config={};
    config.sample_freq_hz=SAMPLE_HZ;config.conv_mode=ADC_CONV_SINGLE_UNIT_1;
    config.format=ADC_DIGI_OUTPUT_FORMAT_TYPE2;config.pattern_num=1;config.adc_pattern=&pattern;
    if(error_==ESP_OK)error_=adc_continuous_config(adc_,&config);
    adc_continuous_evt_cbs_t callbacks={};callbacks.on_pool_ovf=overflow;
    if(error_==ESP_OK)error_=adc_continuous_register_event_callbacks(adc_,&callbacks,this);
    if(error_==ESP_OK)error_=adc_continuous_start(adc_);
    ready_=error_==ESP_OK;
    if(!ready_)closeAdc();
    seenOverflows_=overflowCount();resetWindow();return ready_;
  }
  bool recover() {
    discontinuity();closeAdc();
    const bool ok=initAdc();retryAt_=esp_timer_get_time()+1000000;return ok;
  }
  void process(const uint8_t *buffer,uint32_t bytes) {
    // Reject malformed/foreign frames as sample loss, rather than silently
    // compressing timestamps by skipping samples and inventing faster RPM.
    if(!bytes || bytes%SOC_ADC_DIGI_RESULT_BYTES){++invalidFrames_;discontinuity();return;}
    for(uint32_t i=0;i<bytes;i+=SOC_ADC_DIGI_RESULT_BYTES) {
      const auto *sample=reinterpret_cast<const adc_digi_output_data_t *>(buffer+i);
      if(sample->type2.unit!=0 || sample->type2.channel!=channel_) {
        ++invalidFrames_;discontinuity();return;
      }
    }
    const int64_t started=esp_timer_get_time();
    uint16_t marks=takeMarks();
    for(uint32_t i=0;i<bytes;i+=SOC_ADC_DIGI_RESULT_BYTES) {
      const uint16_t value=reinterpret_cast<const adc_digi_output_data_t *>(buffer+i)->type2.data;
      ring_.record(value|marks);marks=0;
      detector_.feed(value);
      last_=value;sum_+=value;++count_;++samples_;
      minimum_=std::min(minimum_,uint32_t(value));maximum_=std::max(maximum_,uint32_t(value));
    }
    const uint32_t duration=uint32_t(esp_timer_get_time()-started);
    processingUs_+=duration;maxBatchUs_=std::max(maxBatchUs_,duration);
  }
  void command(const Command &c) {
    bool ok=true;
    switch(c.action) {
      case Action::Enabled:detector_.setEnabled(c.value);break;
      case Action::Reset:discontinuity();break;
      case Action::Pin:
        if(c.value<1 || c.value>10){ok=false;break;}
        closeAdc();pin_=c.value;suspended_=false;discontinuity();ok=initAdc();break;
      case Action::Suspend:
        if(!ready_ || suspended_){ok=false;break;}
        error_=adc_continuous_stop(adc_);ok=error_==ESP_OK;
        if(ok){ready_=false;suspended_=true;}
        break;
      case Action::Resume:
        if(!suspended_ || !adc_){ok=false;break;}
        suspended_=false;discontinuity();
        error_=adc_continuous_flush_pool(adc_);
        if(error_==ESP_OK)error_=adc_continuous_start(adc_);
        ready_=error_==ESP_OK;ok=ready_;seenOverflows_=overflowCount();
        break;
    }
    publish(true);
    const Reply reply{c.id,ok};
    if(xQueueSend(replies_,&reply,0)!=pdTRUE)++lostEvents_;
  }
  void publish(bool force=false) {
    const int64_t now=esp_timer_get_time();
    const bool changed=detector_.resultRevision!=previousRevision_ || detector_.phase!=previousPhase_ || detector_.signalFault!=previousFault_;
    if(!force && !changed && now-lastPublish_<10000)return;
    Snapshot s;
    s.phase=detector_.phase;s.ended=detector_.ended;s.ready=ready_;s.suspended=suspended_;
    s.enabled=detector_.enabled;s.valid=detector_.resultValid;s.signalFault=detector_.signalFault;
    s.pin=pin_;s.error=error_;s.samples=samples_;s.detectorUs=detector_.nowUs;
    s.ringCount=ring_.count();s.ringFirst=ring_.first();
    s.revision=detector_.resultRevision;s.launches=detector_.launches;s.revolutions=detector_.revolutions;
    s.edges=detector_.opticalEdges;s.weak=detector_.weakWindows;s.slow=detector_.slowWindows;
    s.shape=detector_.rejectedShape;s.inconsistent=detector_.inconsistentWindows;
    s.rearmExtensions=detector_.rearmExtensions;s.rearmMs=detector_.rearmMs();
    s.last=last_;s.mean=mean_;s.rate=rate_;s.minimum=displayMin_;s.maximum=displayMax_;
    s.processingPercent=processingPercent_;s.overflows=overflowCount();s.readErrors=readErrors_;
    s.invalidFrames=invalidFrames_;s.lostEvents=lostEvents_;s.maxBatchUs=maxBatchUs_;
    s.maxReadGapUs=maxReadGapUs_;s.stackFree=uxTaskGetStackHighWaterMark(nullptr);
    s.resultRpm=detector_.resultRpm;s.peakRpm=detector_.peakRpm;s.candidateRpm=detector_.candidateRpm;
    s.noise=detector_.noiseBand;s.amplitude=detector_.peakAmplitude;s.startNoise=detector_.startNoiseBand;
    s.contrast=detector_.signalContrast;s.hysteresis=detector_.hysteresis;
    portENTER_CRITICAL(&snapshotMux_);snapshot_=s;portEXIT_CRITICAL(&snapshotMux_);
    if(changed && xQueueSend(events_,&s,0)!=pdTRUE)++lostEvents_;
    previousRevision_=s.revision;previousPhase_=s.phase;previousFault_=s.signalFault;lastPublish_=now;
  }
  void run() {
    StickS3SensorProfile::configure(detector_);initAdc();publish(true);
    alignas(4) uint8_t buffer[1024];
    for(;;) {
      Command c;
      while(xQueueReceive(commands_,&c,0)==pdTRUE)command(c);
      if(!ready_) {
        if(!suspended_ && esp_timer_get_time()>=retryAt_)recover();
        publish();vTaskDelay(pdMS_TO_TICKS(10));continue;
      }
      if(overflowCount()!=seenOverflows_){recover();publish(true);continue;}
      uint32_t bytes=0;
      error_=adc_continuous_read(adc_,buffer,sizeof(buffer),&bytes,10);
      if(error_==ESP_ERR_TIMEOUT){error_=ESP_OK;publish();continue;}
      if(error_!=ESP_OK){++readErrors_;recover();publish(true);continue;}
      if(overflowCount()!=seenOverflows_){recover();publish(true);continue;}
      const int64_t now=esp_timer_get_time();
      if(lastRead_)maxReadGapUs_=std::max(maxReadGapUs_,uint32_t(now-lastRead_));
      lastRead_=now;process(buffer,bytes);
      if(overflowCount()!=seenOverflows_){recover();publish(true);continue;}
      const int64_t elapsed=esp_timer_get_time()-windowStart_;
      if(elapsed>=500000) {
        mean_=count_?float(sum_)/count_:0;rate_=count_*1000000.0f/elapsed;
        processingPercent_=float(processingUs_)*100/elapsed;
        displayMin_=minimum_;displayMax_=maximum_;resetWindow();
      }
      publish();
    }
  }
};

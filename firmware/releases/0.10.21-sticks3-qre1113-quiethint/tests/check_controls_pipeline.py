#!/usr/bin/env python3
"""Exercise actual sketch navigation/edit handlers with host peripherals."""
from pathlib import Path
import os
import subprocess
import tempfile

root=Path(__file__).resolve().parents[1]
source=(root/'LaunchLabMini/LaunchLabMini.ino').read_text()
def function(name):
    start=source.index('static void '+name+'(')
    # Some handlers have a forward declaration before their definition.
    while source.index(';',start)<source.index('{',start):
        start=source.index('static void '+name+'(',start+1)
    cursor=source.index('{',start)+1
    depth=1
    while depth:
        depth+=(source[cursor]=='{')-(source[cursor]=='}')
        cursor+=1
    return source[start:cursor]
prefix=r'''
#include "controls.h"
#include "analog_tachometer.h"
#include "rpm_estimator_setting.h"
#include "display_flip_setting.h"
#include "sensor_profile_setting.h"
#include "power_status.h"
#include "practice_ui.h"
#include "launch_feedback.h"
#include <cassert>
#include <iostream>
'''
# practice_ui.h needs graphics types only for its inline renderer. This fixture
# tests actions, so use the actual practice data and view types directly.
prefix=prefix.replace('#include "practice_ui.h"','#include "practice_history.h"\n#include "practice_views.h"')
practice_ui=(root/'LaunchLabMini/practice_ui.h').read_text()
prefix+=practice_ui[practice_ui.index('namespace PracticeUI {'):practice_ui.index('inline void draw(')]+'}\n'
prefix+=r'''
static uint32_t millis(){return 10000;}
using Controls::Page;
static Controls::State controls;
static bool tournamentMode=false,historyPage=false,dirty=false,diagnostics=false,demo=false,motionDemo=false,motionPending=false,settingsSaveError=false,restorePreview=false,displayFlipped=false;
static uint8_t brightnessPercent=40;
static uint32_t historyOffset=0,newSessionAt=0,tournamentHintUntil=0;
enum class TournamentView:uint8_t{RecordingOnly,Rpm};
static TournamentView tournamentView=TournamentView::RecordingOnly;
static const char *tournamentViewName(){return tournamentView==TournamentView::Rpm?"rpm":"recording_only";}
static PracticeUI::View historyView=PracticeUI::View::Recent;
static PracticeHistory practice,demoPractice;
static struct {uint32_t number=1;} latestMotion;
static LaunchFeedback launchFeedback;
static InactivityTimer inactivity;
static RpmEstimator::Mode rpmEstimator=RpmEstimator::DEFAULT_MODE;
static StickS3SensorProfile::Mode sensorProfile=StickS3SensorProfile::DEFAULT_MODE;
struct Prefs:Preferences {
  unsigned writes=0;
  size_t putUChar(const char *key,uint8_t value){++writes;return putBytes(key,&value,1);}
  size_t putBytes(const char *key,const void *data,size_t size){++writes;return Preferences::putBytes(key,data,size);}
}prefs;
static uint8_t backlightValue(){return (unsigned(brightnessPercent)*255+50)/100;}
struct Snapshot{AnalogTachometer::Phase phase=AnalogTachometer::Phase::Ready;uint32_t launches=0;};
enum class Action{IdleCheckpointBegin,CheckpointEnd,Estimator,SensorProfile};
struct Acquisition {
  Snapshot state;unsigned begins=0,ends=0,estimatorChanges=0,profileChanges=0;bool failEstimator=false,failProfile=false;
  Snapshot snapshot(){return state;}
  bool request(Action action,uint32_t expected=0){
    if(action==Action::IdleCheckpointBegin){if(state.phase==AnalogTachometer::Phase::Launch || expected!=state.launches)return false;++begins;}
    if(action==Action::CheckpointEnd)++ends;
    if(action==Action::Estimator){++estimatorChanges;return !failEstimator;}
    if(action==Action::SensorProfile){++profileChanges;return !failProfile;}
    return true;
  }
}acquisition;
struct {struct {unsigned brightness=102,rotation=0;void setBrightness(unsigned value){brightness=value;}void setRotation(unsigned value){rotation=value;}}Display;}M5;
struct {template<class... T>void printf(const char*,T...){}void println(const char*){}}Serial;
'''
tests=r'''
static void reset(){
  controls={};tournamentMode=historyPage=dirty=diagnostics=demo=motionDemo=motionPending=settingsSaveError=restorePreview=displayFlipped=false;
  historyOffset=newSessionAt=tournamentHintUntil=0;historyView=PracticeUI::View::Recent;tournamentView=TournamentView::RecordingOnly;
  practice={};demoPractice={};latestMotion={};launchFeedback={};inactivity={};brightnessPercent=40;rpmEstimator=RpmEstimator::DEFAULT_MODE;sensorProfile=StickS3SensorProfile::DEFAULT_MODE;
  acquisition={};prefs={};M5.Display.brightness=102;M5.Display.rotation=0;
  Preferences::data.clear();Preferences::zeroLengthKeys.clear();Preferences::failWrite=Preferences::shortRead=false;
  assert(prefs.begin("controls-test",false));
}
static void edit(unsigned row){controls.page=Page::Settings;controls.setting=row;syncNavigation();buttonA();assert(controls.page==Page::Edit);}
int main(){
  reset();buttonA();holdB();assert(!launchFeedback.shown() && controls.page==Page::Main);
  reset();edit(2);acquisition.state.phase=AnalogTachometer::Phase::Launch;buttonB();
  assert(controls.draft==50 && brightnessPercent==40 && M5.Display.brightness==102 && restorePreview);
  acquisition.state.phase=AnalogTachometer::Phase::Ready;previewSetting();
  assert(M5.Display.brightness==128 && !restorePreview);holdB();assert(M5.Display.brightness==102 && !prefs.writes);
  reset();buttonA();assert(launchFeedback.shown());buttonB();assert(!launchFeedback.shown() && controls.page==Page::Menu);
  buttonA();assert(controls.page==Page::HistoryMenu);buttonA();assert(controls.page==Page::History);
  assert(practice.accept(1,true,6000,millis()));buttonB();holdB();assert(controls.page==Page::HistoryMenu);
  holdB();holdB();assert(controls.page==Page::Main && !historyPage);
  reset();edit(2);buttonB();assert(controls.draft==50 && brightnessPercent==40 && M5.Display.brightness==128 && !prefs.writes);
  holdB();assert(controls.page==Page::Settings && brightnessPercent==40 && M5.Display.brightness==102 && !prefs.writes);
  edit(2);buttonB();buttonA();assert(controls.page==Page::Settings && brightnessPercent==50 && M5.Display.brightness==128 && prefs.writes && !settingsSaveError);
  assert(acquisition.begins==acquisition.ends);
  reset();edit(3);buttonB();assert(!displayFlipped && M5.Display.rotation==2 && !prefs.writes);
  holdB();assert(M5.Display.rotation==0 && !prefs.writes);
  edit(3);buttonB();Preferences::failWrite=true;buttonA();assert(controls.page==Page::Edit && settingsSaveError && !displayFlipped);
  Preferences::failWrite=false;buttonA();assert(controls.page==Page::Settings && displayFlipped && M5.Display.rotation==2);
  reset();edit(0);for(unsigned i=0;i<7;++i)buttonB();assert(controls.draft==10 && inactivity.minutes()==3 && !prefs.writes);
  acquisition.state.phase=AnalogTachometer::Phase::Launch;buttonA();assert(controls.page==Page::Edit && !prefs.writes && settingsSaveError);
  acquisition.state.phase=AnalogTachometer::Phase::Ready;buttonA();assert(inactivity.minutes()==10 && controls.page==Page::Settings);
  reset();assert(practice.accept(1,true,6000,millis()));const auto session=practice.session()->number;
  edit(1);buttonB();assert(rpmEstimator==RpmEstimator::Mode::ThreeTurn && practice.session()->number==session);
  holdB();assert(practice.accept(2,true,6100,millis()) && practice.session()->number==session);
  edit(1);buttonB();buttonA();assert(rpmEstimator==RpmEstimator::Mode::SingleTurn && acquisition.estimatorChanges==1);
  assert(practice.accept(3,true,6200,millis()) && practice.session()->number==session+1 && practice.size()==3);
  reset();edit(1);buttonB();acquisition.failEstimator=true;buttonA();assert(controls.page==Page::Edit && rpmEstimator==RpmEstimator::Mode::ThreeTurn && settingsSaveError);
  RpmEstimator::Mode saved;assert(RpmEstimatorSetting::load(prefs,saved) && saved==rpmEstimator);
  reset();assert(practice.accept(1,true,6000,millis()));const auto profileSession=practice.session()->number;
  edit(4);buttonB();assert(controls.draft==1 && sensorProfile==StickS3SensorProfile::Mode::Standard && !prefs.writes);
  holdB();assert(sensorProfile==StickS3SensorProfile::Mode::Standard && !prefs.writes && !acquisition.profileChanges);
  edit(4);buttonB();acquisition.state.phase=AnalogTachometer::Phase::Launch;buttonA();
  assert(controls.page==Page::Edit && settingsSaveError && !prefs.writes && !acquisition.profileChanges);
  acquisition.state.phase=AnalogTachometer::Phase::Ready;buttonA();
  assert(controls.page==Page::Settings && sensorProfile==StickS3SensorProfile::Mode::Tcrt && acquisition.profileChanges==1);
  StickS3SensorProfile::Mode profileSaved;
  assert(SensorProfileSetting::load(prefs,profileSaved) && profileSaved==sensorProfile);
  assert(practice.accept(2,true,6100,millis()) && practice.session()->number==profileSession+1);
  const auto writes=prefs.writes;edit(4);buttonA();assert(acquisition.profileChanges==1 && prefs.writes==writes);
  reset();edit(4);buttonB();acquisition.failProfile=true;buttonA();
  assert(controls.page==Page::Edit && settingsSaveError && sensorProfile==StickS3SensorProfile::Mode::Standard);
  assert(SensorProfileSetting::load(prefs,profileSaved) && profileSaved==sensorProfile);
  reset();edit(4);buttonB();Preferences::failWrite=true;buttonA();
  assert(controls.page==Page::Edit && settingsSaveError && !acquisition.profileChanges && sensorProfile==StickS3SensorProfile::Mode::Standard);
  Preferences::failWrite=false;buttonA();assert(sensorProfile==StickS3SensorProfile::Mode::Tcrt && !settingsSaveError);
  assert(acquisition.begins==acquisition.ends);
  reset();holdA();assert(tournamentMode && tournamentView==TournamentView::RecordingOnly);
  buttonA();holdB();assert(tournamentMode && !launchFeedback.shown());buttonB();assert(tournamentView==TournamentView::Rpm);
  holdA();assert(!tournamentMode && controls.page==Page::Main);
  reset();edit(3);buttonB();cancelSettingEdit();syncNavigation();assert(controls.page==Page::Settings && M5.Display.rotation==0 && !prefs.writes);
  std::cout<<"PASS: actual control handlers; menu/back, recap, preview rollback, persistence retry, active-pull guard, metric/session boundary, rollback and tournament lock\n";
}
'''
names=['syncNavigation','toggleFeedback','previewSetting','cancelSettingEdit','commitSetting','newSession','browseOlder','navigate','buttonA','buttonB','holdA','holdB']
with tempfile.TemporaryDirectory(prefix='launchlab-controls-') as directory:
    directory=Path(directory);cpp=directory/'test.cpp';exe=directory/'test'
    cpp.write_text(prefix+'\n'.join(function(name) for name in names)+tests)
    subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                    '-I'+str(root/'tests/fakes'),'-I'+str(root/'LaunchLabMini'),'-I'+str(root/'LaunchLabRpm'),str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)

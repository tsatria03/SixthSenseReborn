"""``AppDelegate`` - global state and the whole of the game's sound dispatch.

Everything that makes a noise goes through ``playSound:Gain:Pos:z:reprats:`` (0x6658),
and that method is three lines:

    -(void)playSound:(int)num Gain:(float)g Pos:(CGPoint)p z:(int)z reprats:(BOOL)r {
        int i = [self playSoundBufNumber:num];
        if ([[aSoundBufControlData objectAtIndex:i] bIsPlaying])
            [playback stopSound:i];
        [playback queueNote:i gain:g sourcePos:p defaultZ:z repeats:r];
        [playback startSound:i Postion:p];
    }

``playSoundBufNumber:`` (0x6370) is the voice allocator.  ``aSoundBufControlData`` is a
growing array of ``SoundListControl``; the index of an entry *is* the OpenAL note, so a
sound number keeps the same note for as long as its entry survives:

    int i = [self CheckSoundBuf:num];          // entry already holding this sound number
    if (i == -1) {
        int free = [self findBufFlagNO];       // first entry with bIsPlaying == NO
        ctl = [SoundListControl new];
        ctl.bIsPlaying  = YES;
        ctl.iFileNumber = num;
        ctl.sFileName   = [self returnFileName:num];      // SoundList.plist[num]
        if (free == -1) { i = count; [aSoundBufControlData addObject:ctl]; }
        else            { i = free;  [aSoundBufControlData replaceObjectAtIndex:free withObject:ctl];
                          [playback freeSourceOne:i]; [playback freeBufferOne:i]; }
        [playback initBufferOne:i FileName:ctl.sFileName Type:@"wav"];
        [playback initSourceOne:i];
    } else {
        [[aSoundBufControlData objectAtIndex:i] setBIsPlaying:YES];
    }
    return i;

Consequence worth knowing when reading the monster code: *one sound number is one voice*.
Two monsters given the same ``comingSound`` share a source and cut each other off, which
is why ``SoundList.plist`` lists each zombie sample three times (93, 94, 95 are all
``zombie_1_coming_cave``) and ``-[Stage_1_E MonsterInit:]`` hands out one of the three.

Numbers are spoken digit by digit from the ``zero``..``nine`` WAVs, one per second, by
``TTSNumber:type:`` (0x5590) feeding ``readNumber:`` (0x5cbc) off ``ttsTimer``.
"""
from __future__ import annotations

import logging
import os
import plistlib

from .. import paths
from ..platform import volume
from ..platform.defaults import UserDefaults
from ..platform.runloop import RunLoop
from .oal_playback import OalPlayback
from . import weapon_stats
from .sound_list_control import SoundListControl

log = logging.getLogger('app')

#: PORT ADDITION: the menu music, and the save key for its volume (change_menu_music_volume).
MENU_MUSIC_TRACK = 'bgm_main_menu'
MENU_MUSIC_KEY = volume.MENU_MUSIC_KEY



class AppDelegate:
    """The singleton the whole game reaches through ``[[UIApplication sharedApplication]
    delegate]`` (``sub_3ccc`` in the listings)."""

    _instance = None

    @classmethod
    def shared(cls):
        if cls._instance is None:
            cls._instance = AppDelegate()
        return cls._instance

    def __init__(self):
        AppDelegate._instance = self
        self.ttsTimer = None
        self.ttsArrayCount = 0
        self.tts_type = 0
        self.mode = 1                  # voice over on, see saved_mode
        self.playback = None
        self.numberBackUp = []
        self.haveGold = 0
        self.haveWeapon = []
        self.stage = 0
        self.aSoundBufControlData = []
        self.bDevice = False           # "does this device vibrate"
        self.useWeapon = []
        self.CheckVoiceOver = False
        self.bCall = False
        self.bPriceCheck = False
        self.iPodIsPlaying = False
        self._sound_list = None
        self.mainNaviController = None
        # Not in the original: --debug.  Nothing hurts you and nothing you kill
        # counts, so no score, gold or top score comes of it (Stage_1_E).
        self.debug = False
        # PORT ADDITION: a controller's motors (ui/vibration.py).  The frame loop sets it;
        # without one, which is every test, nothing vibrates.
        self.vibration = None

    # -[AppDelegate application:didFinishLaunchingWithOptions:] 0x3f64
    def didFinishLaunching(self):
        self.playback = OalPlayback()
        self.aSoundBufControlData = []
        d = UserDefaults.standardUserDefaults()
        self.haveGold = d.intForKey_('GOLD')
        self.stage = d.intForKey_('STAGE')
        self.mode = self.saved_mode()
        self.CheckVoiceOver = bool(self.mode)
        # PORT ADDITION (2026-09-25): the volume settings, and settings.json written with
        # every one at its default, voice over included, so a player sees what they can
        # change (aidocks/project_volume_settings_plan.md)
        wrote = volume.load(d)
        if d.objectForKey_('EYEMODE') is None:
            d.setObject_forKey_(str(self.mode), 'EYEMODE')
            wrote = True
        if wrote:
            d.synchronize()
        self.weaponHave()
        return True

    # ================================================================== mode
    def saved_mode(self):
        """``EYEMODE``: 1 is voice over on, the game's own recordings, and 0 is voice
        over off, where the menus speak through the screen reader instead.

        **DIVERGENCE:** a save that has never set it starts with voice over on.  The
        original fell back to ``DEFAULTEYEMODE``, which nothing writes, so a new player
        got mode 0, the standard screens the iPhone's VoiceOver read."""
        d = UserDefaults.standardUserDefaults()
        if d.objectForKey_('EYEMODE') is None:
            return 1
        return 1 if d.intForKey_('EYEMODE') == 1 else 0

    # ================================================================ vibration
    @property
    def vibration_on(self):
        """PORT ADDITION: ``VIBRATION`` in settings.json, '1' or '0'; a save that has
        never set it vibrates."""
        return UserDefaults.standardUserDefaults().stringForKey_('VIBRATION') != '0'

    def set_vibration(self, on):
        """Save the setting; turning it off silences the motors at once."""
        d = UserDefaults.standardUserDefaults()
        d.setObject_forKey_('1' if on else '0', 'VIBRATION')
        d.synchronize()
        if not on:
            self.vibrate_stop()

    @property
    def screen_reader(self):
        """Voice over is off, so the menus speak through the screen reader."""
        return self.mode == 0

    # ================================================================ sounds
    @property
    def sound_list(self):
        if self._sound_list is None:
            p = paths.path_for_resource('SoundList', 'plist')
            with open(p, 'rb') as f:
                self._sound_list = plistlib.load(f)
        return self._sound_list

    # -[AppDelegate returnFileName:] 0x61dc
    #   return [[NSArray arrayWithContentsOfFile:SoundList.plist] objectAtIndex:num];
    def returnFileName_(self, num):
        sl = self.sound_list
        if 0 <= num < len(sl):
            return sl[num]
        return None

    # -[AppDelegate CheckSoundBuf:] 0x625c
    def CheckSoundBuf_(self, num):
        for i, ctl in enumerate(self.aSoundBufControlData):
            if ctl.iFileNumber == num:
                return i
        return -1

    # -[AppDelegate findBufFlagNO] 0x62e8
    def findBufFlagNO(self):
        for i, ctl in enumerate(self.aSoundBufControlData):
            if not ctl.bIsPlaying:
                return i
        return -1

    # -[AppDelegate playSoundBufNumber:] 0x6370
    def playSoundBufNumber_(self, num):
        i = self.CheckSoundBuf_(num)
        if i == -1:
            free = self.findBufFlagNO()
            ctl = SoundListControl()
            ctl.bIsPlaying = True
            ctl.iFileNumber = num
            ctl.sFileName = self.returnFileName_(num)
            if free == -1:
                i = len(self.aSoundBufControlData)
                self.aSoundBufControlData.append(ctl)
            else:
                i = free
                self.aSoundBufControlData[free] = ctl
                self.playback.freeSourceOne_(i)
                self.playback.freeBufferOne_(i)
            if ctl.sFileName:
                self.playback.initBufferOne_FileName_Type_(i, ctl.sFileName, 'wav')
            self.playback.initSourceOne_(i)
        else:
            self.aSoundBufControlData[i].bIsPlaying = True
        return i

    # -[AppDelegate stopSoundBufNumber:] 0x6580
    def stopSoundBufNumber_(self, num):
        if len(self.aSoundBufControlData) < 1:
            return
        i = self.CheckSoundBuf_(num)
        if i == -1:
            return
        self.playback.stopSound_(i)
        self.aSoundBufControlData[i].bIsPlaying = False

    # -[AppDelegate playSound:Gain:Pos:z:reprats:] 0x6658
    def playSound_Gain_Pos_z_reprats_(self, num, gain, pos, z, repeats):
        i = self.playSoundBufNumber_(num)
        if self.aSoundBufControlData[i].bIsPlaying:
            self.playback.stopSound_(i)
        self.playback.queueNote_gain_sourcePos_defaultZ_repeats_(i, gain, pos, z, repeats)
        self.playback.startSound_Postion_(i, pos)

    def playOverlapSound_Gain_Pos_z_(self, num, gain, pos, z):
        """PORT ADDITION: ``playSound:`` that does not restart the sound if it is still
        playing, for the MG80's burst (``OalPlayback.playOverlap_gain_pos_z_``)."""
        i = self.playSoundBufNumber_(num)
        self.playback.playOverlap_gain_pos_z_(i, gain, pos, z)

    def vibrate_effect(self, name):
        """PORT ADDITION: start a named effect on the controller, if there is one.  Not
        ``vibrate``, the original's phone buzz when zombie 8 grabs you, which the port
        leaves as it was."""
        if self.vibration is not None:
            self.vibration.play(name)

    def vibrate_kill(self, distance, kind='kill'):
        """PORT ADDITION: a zombie killed ``distance`` cm away; the closer, the heavier."""
        if self.vibration is not None:
            self.vibration.play_kill(distance, kind)

    def vibrate_zombie(self, kind):
        """PORT ADDITION: a zombie's blow on you, by its ``monsterNumber``."""
        if self.vibration is not None:
            self.vibration.play_zombie(kind)

    def vibrate_stop(self):
        """PORT ADDITION: silence the motors, for a pause or leaving a stage."""
        if self.vibration is not None:
            self.vibration.stop()

    def playHitSound_Gain_Pos_z_(self, num, gain, pos, z):
        """PORT DIVERGENCE (tunmi13productions, 2026-09-27): a weapon's hit on a monster, queued
        with the monster's own distances (``MonsterQueueNote:``, reference 100, maximum
        1600) instead of ``playSound:``'s 40 and 800, so it fades as the monster does
        rather than 2.5 times sooner.  The original plays every hit through
        ``playSound:`` (0x6658); aidocks/project_sound_trims_plan.md has why."""
        i = self.playSoundBufNumber_(num)
        if self.aSoundBufControlData[i].bIsPlaying:
            self.playback.stopSound_(i)
        self.playback.MonsterQueueNote_gain_sourcePos_defaultZ_repeats_(i, gain, pos, z, False)
        self.playback.startSound_Postion_(i, pos)
    # ==================================================== spoken numbers (TTS)
    # -[AppDelegate TTSNumber:type:] 0x5590
    def TTSNumber_type_(self, number, type_):
        """Queue ``number`` to be read out one digit per second, then the unit word."""
        self.tts_type = type_
        s = '%d' % number
        self.numberBackUp = []
        n = number
        # readNumber_ (0x5cbc) decrements ttsArrayCount and reads
        # numberBackUp[ttsArrayCount], so the first digit spoken is the one at the
        # *last* index. Build the array least-significant-digit first, so that
        # last index holds the most significant digit and it is spoken first
        # (10 must read "one, zero", not "zero, one").
        if n == 0:
            self.numberBackUp.append('0')
        while n > 0:
            self.numberBackUp.append(str(n % 10))
            n //= 10
        self.ttsArrayCount = len(self.numberBackUp)
        if self.ttsTimer is None or not self.ttsTimer.isValid():
            self.ttsTimer = RunLoop.main().scheduledTimer(
                1.0, self, 'readNumber_', None, True)
        return s

    # -[AppDelegate TTSNumber:type2:] 0x583c - the same, feeding readTimeSec instead.
    def TTSNumber_type2_(self, number, type_):
        return self.TTSNumber_type_(number, type_)

    # -[AppDelegate readNumber:] 0x5cbc
    def readNumber_(self, timer=None):
        if self.ttsArrayCount >= 1:
            self.ttsArrayCount -= 1
            digit = int(self.numberBackUp[self.ttsArrayCount])
            self.playSound_Gain_Pos_z_reprats_(digit, 0.2, (0.0, 0.0), 0, False)
            return
        if self.ttsTimer is not None and self.ttsTimer.isValid():
            self.ttsTimer.invalidate()
            self.ttsTimer = None
        self.numberBackUp = []

    # -[AppDelegate readStop] 0x5ae8
    def readStop(self):
        for digit in range(10):
            self.playback.stopSound_(self.playSoundBufNumber_(digit))
        if self.ttsTimer is not None and self.ttsTimer.isValid():
            self.ttsTimer.invalidate()
        self.ttsTimer = None
        self.numberBackUp = []

    # ================================================================ weapons
    # -[AppDelegate weaponHave] 0x4ee8
    def weaponHave(self):
        d = UserDefaults.standardUserDefaults()
        # grenade, knife and colt are always owned (0x4f4e: three literal @"1"s)
        self.haveWeapon = ['1', '1', '1']
        for key in ('SHOTGUN', 'M4', 'AK47', 'MG80', 'JAPAN'):
            self.haveWeapon.append('1' if d.intForKey_(key) >= 1 else '0')

        self.useWeapon = []
        for key in ('GRENADEUSE', 'KNIFEUSE', 'COLTUSE', 'SHOTGUNUSE',
                    'M4USE', 'AK47USE', 'MG80USE', 'JAPANUSE'):
            self.useWeapon.append('1' if d.intForKey_(key) >= 1 else '0')

        # 0x52xx: a fresh install has nothing equipped, so grenade, knife and colt
        # are switched on and written back.
        if not any(v == '1' for v in self.useWeapon):
            for key in ('GRENADEUSE', 'KNIFEUSE', 'COLTUSE'):
                d.setObject_forKey_('1', key)
            d.synchronize()
            self.useWeapon[0] = self.useWeapon[1] = self.useWeapon[2] = '1'

        # PORT ADDITION (2026-09-25): the stats a weapon's page speaks, written into the
        # save for every weapon owned or equipped that has none yet, and never read back
        # (weapon_stats.py).  This runs on every start, after buying and after equipping.
        if weapon_stats.fill(d, self.haveWeapon, self.useWeapon):
            d.synchronize()

    # ================================================================== music
    # -[AppDelegate BGMusicStart] 0x4ce4 / -[AppDelegate BGMusicStop] 0x4d30
    def BGMusicStart(self):
        """The menu music.  PORT ADDITION: the original's ``MainController`` never starts
        music - the only caller in the binary is ``-[Stage_1_E GameEndAction:]`` (0x330da) -
        so there is no gain of its own to copy, and ``volume.MENU_MUSIC_DB`` is the whole
        value.  It started at 1.0, which talked over the rows the menu reads aloud."""
        if self.playback:
            self.playback.startBGPlayer_type_soundGain_Loop_(
                MENU_MUSIC_TRACK, 'wav', volume.menu_music(self.menu_music_volume), True)

    def BGMusicStop(self):
        if self.playback:
            self.playback.backgroundSoundStop()

    # PORT ADDITION (tsatria03, 2026-09-25): Page Up and Page Down on the menu screens set
    # the menu music's volume, 0 to 100% in steps of 10, saved as MENUMUSICVOLUME.  Only
    # the menu music: the level music, the ambience and the story's music keep the
    # binary's gains.  aidocks/project_menu_music_volume_plan.md has the plan.
    @property
    def menu_music_volume(self):
        """The saved menu music volume, any whole percentage from 0 to 100 since it can be
        set by hand in settings.json; 100 when unset or not one."""
        return volume.percent(UserDefaults.standardUserDefaults().objectForKey_(MENU_MUSIC_KEY))

    def menu_music_playing(self):
        """Whether the music player is playing the menu music.  The level music plays on
        the same player, so this is what keeps the keys off it."""
        bg = getattr(self.playback, 'bgPlayer', None)
        if bg is None or not bg.path:
            return False
        name = os.path.splitext(os.path.basename(bg.path))[0]
        return name == MENU_MUSIC_TRACK and bg.playing

    def change_menu_music_volume(self, step):
        """Page Up (+1) or Page Down (-1): the next step of ten, holding at 0 and 100,
        saved, and heard at once.  From a value set by hand between two steps it goes to
        the nearer step that way: 55 goes up to 60 and down to 50.  Returns the new
        percentage, or None when the menu music is not playing and nothing changed."""
        if not self.menu_music_playing():
            return None
        percent = volume.step_percent(self.menu_music_volume, step)
        d = UserDefaults.standardUserDefaults()
        d.setInteger_forKey_(percent, MENU_MUSIC_KEY)
        d.synchronize()
        # as startBGPlayer sets it, the master knob included
        self.playback.bgPlayer.set_volume(volume.master(volume.menu_music(percent)))
        return percent

    # PORT ADDITION (tunmi13productions, 2026-09-26): during play Page Up and Page Down set the
    # gameplay gain, and with Shift or Alt the weapons or the player (Control set the
    # entities until 2026-09-28).  aidocks/project_gameplay_gain_plan.md has the plan.
    def change_gameplay_volume(self, key, step):
        """Step ``key`` (``volume.GAMEPLAY_GAIN_KEY`` or one of the two groups) up
        (+1) or down (-1), save it, and apply it at once to everything playing.
        Returns the new value, decibels for the gain and a percentage for a group."""
        if key == volume.GAMEPLAY_GAIN_KEY:
            value = volume.step_gain_db(volume.gameplay_gain_db, step)
            volume.gameplay_gain_db = value
        else:
            value = volume.step_percent(volume.percents[key], step)
            volume.percents[key] = value
        d = UserDefaults.standardUserDefaults()
        d.setInteger_forKey_(value, key)
        d.synchronize()
        if self.playback is not None:
            if key == volume.GAMEPLAY_GAIN_KEY:
                self.playback.setGameplayGain_(True)
            else:
                self.playback.refreshGains()
        return value

    # ``AudioServicesPlaySystemSound(kSystemSoundID_Vibrate)`` in the original.
    def vibrate(self):
        pass

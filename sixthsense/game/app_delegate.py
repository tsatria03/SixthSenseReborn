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

(The original read numbers digit by digit from the ``zero``..``nine`` WAVs with ``TTSNumber:type:``
and ``readNumber:``; the screen reader says them whole now, and that code is gone.)
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
from . import gold_rates, weapon_order, weapon_stats, weapon_upgrades
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
        self.playback = None
        self.haveGold = 0
        self.haveWeapon = []
        self.stage = 0
        self.aSoundBufControlData = []
        self.bDevice = False           # "does this device vibrate"
        self.useWeapon = []
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
        # PORT ADDITION: the attached controllers (ui/controller.py).  The frame loop sets
        # it; without one, which is every test, no pad is attached.
        self.controllers = None
        # PORT ADDITION: shaking a pad that can sense it (ui/shake.py), set by the frame loop.
        self.shake = None

    # -[AppDelegate application:didFinishLaunchingWithOptions:] 0x3f64
    def didFinishLaunching(self):
        self.playback = OalPlayback()
        self.aSoundBufControlData = []
        d = UserDefaults.standardUserDefaults()
        self.haveGold = d.intForKey_('GOLD')
        self.stage = d.intForKey_('STAGE')
        # PORT ADDITION (tsatria03, 2026-10-05): GOLD is written only when it changes, at
        # a game's end and on buying, so a new save had no key to see or edit.  A missing
        # one is written as '0', in the original's text form; gold already there stays.
        gold_missing = d.objectForKey_('GOLD') is None
        if gold_missing:
            d.setObject_forKey_('0', 'GOLD')
        # PORT ADDITION (2026-09-25): the volume settings, and settings.json written with
        # every one at its default, so a player sees what they can change
        # (aidocks/completed/volume_settings_plan.md)
        wrote = volume.load(d)
        # PORT ADDITION (2026-10-05): the gold a game pays, editable (gold_rates.py)
        wrote = gold_rates.fill(d) or wrote
        # and the upgrade levels, caps and settings (weapon_upgrades.py)
        wrote = weapon_upgrades.fill(d) or wrote or gold_missing
        # PORT ADDITION (2026-10-06): the order the weapons come in (weapon_order.py)
        wrote = weapon_order.fill(d) or wrote
        if wrote:
            d.synchronize()
        self.weaponHave()
        return True

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

    # ================================================= the shake and the chosen pad
    # PORT ADDITION (tunmi13productions, 2026-10-06, aidocks/project_settings_menu_plan.md)

    @property
    def shake_on(self):
        """``SHAKE`` in settings.json, '1' or '0': shaking a pad that can sense one shakes
        a zombie off.  A save that has never set it can, since that is how it worked before
        there was a setting (aidocks/completed/controller_shake_plan.md).  A is still the
        shake button whatever this says."""
        return UserDefaults.standardUserDefaults().stringForKey_('SHAKE') != '0'

    def set_shake(self, on):
        d = UserDefaults.standardUserDefaults()
        d.setObject_forKey_('1' if on else '0', 'SHAKE')
        d.synchronize()

    @property
    def controller_choice(self):
        """``CONTROLLER`` in settings.json: the name of the pad the game plays with, or ''
        for whichever is found first.

        **A name, never an id.**  Unplug the pad on id 0 and the next pad plugged in takes
        that id, so an id says nothing between runs (tunmi13productions, 2026-10-06).  A
        saved name that is not attached is left alone, so plugging that pad back in picks
        it up again with nothing for the player to do.
        """
        return UserDefaults.standardUserDefaults().stringForKey_('CONTROLLER') or ''

    def set_controller_choice(self, name):
        d = UserDefaults.standardUserDefaults()
        d.setObject_forKey_(name or '', 'CONTROLLER')
        d.synchronize()

    def can_shake_now(self):
        """Whether a shake would do anything: the player has it on and the chosen pad can
        sense one.  ``can_shake`` alone ignores the setting, for the Settings screen."""
        return self.shake_on and self.can_shake()

    # ======================================================== the headshot settings
    @property
    def headshot_speech_on(self):
        """PORT ADDITION: ``HEADSHOTSPEECH`` in settings.json, '1' or '0': the screen reader
        says "Headshot!".  A save that has never set it does."""
        return UserDefaults.standardUserDefaults().stringForKey_('HEADSHOTSPEECH') != '0'

    @property
    def headshot_beep_on(self):
        """PORT ADDITION: ``HEADSHOTBEEP`` in settings.json, '1' or '0': a beep where the
        zombie is on every headshot.  A save that has never set it has no beep."""
        return UserDefaults.standardUserDefaults().stringForKey_('HEADSHOTBEEP') == '1'

    def set_headshot_speech(self, on):
        d = UserDefaults.standardUserDefaults()
        d.setObject_forKey_('1' if on else '0', 'HEADSHOTSPEECH')
        d.synchronize()

    def set_headshot_beep(self, on):
        d = UserDefaults.standardUserDefaults()
        d.setObject_forKey_('1' if on else '0', 'HEADSHOTBEEP')
        d.synchronize()

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

    def controller_name(self):
        """PORT ADDITION: the name of the first attached controller, or None with none."""
        pads = self.controllers.pads if self.controllers is not None else []
        if not pads:
            return None
        return getattr(pads[0], 'name', None) or 'controller'

    def can_shake(self):
        """PORT ADDITION: whether an attached controller can be shaken, a DualSense for one."""
        return self.shake is not None and self.shake.capable()

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

    def vibrate_headshot(self, distance):
        """PORT ADDITION: a headshot on a zombie ``distance`` cm away; the closer, the stronger."""
        if self.vibration is not None:
            self.vibration.play_headshot(distance)

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
        ``playSound:`` (0x6658); aidocks/completed/sound_trims_plan.md has why."""
        i = self.playSoundBufNumber_(num)
        if self.aSoundBufControlData[i].bIsPlaying:
            self.playback.stopSound_(i)
        self.playback.MonsterQueueNote_gain_sourcePos_defaultZ_repeats_(i, gain, pos, z, False)
        self.playback.startSound_Postion_(i, pos)
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

        # PORT ADDITION (2026-10-05): every weapon's stats in the save, which the pages
        # read out and the stage plays with; missing or unusable ones are put back to the
        # real numbers (weapon_stats.py).  This runs on every start, after buying and
        # after equipping.
        if weapon_stats.fill(d):
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
    # binary's gains.  aidocks/completed/menu_music_volume_plan.md has the plan.
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
    # entities until 2026-09-28).  aidocks/completed/gameplay_gain_plan.md has the plan.
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

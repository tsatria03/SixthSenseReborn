"""The shop: its front menu, the weapon list and a weapon's own page.

    -[mainStoreController ...]    0x1c8c8..0x1ef58    the shop's front menu
    -[StoreController ...]        0x12f88..0x16cd0    the weapon list
    -[DetailStoreController ...]  0x18b20..0x1c7c4    one weapon: its stats and Buy

Gold is local - ``NSUserDefaults`` key ``GOLD``, which ``Stage_1_E`` pays into at the
end of a run - so buying a weapon works here exactly as it did on the phone.  The two
things that do not are the gold store and the coin store, which were in-app purchases,
*Purchase all weapons*, which was the StoreKit product ``SixthSense.AllWeapon``, and
restore purchases.  The game leaves all four rows out: Apple's
in-app purchases no longer exist, and there are no recordings for buying any of them with
gold instead.

The weapon table below is not data: ``-[DetailStoreController viewDidLoad]`` sets it
out weaponType by weaponType in code (0x192f2..0x1a0ec).  The original's numbers there
were not the ones it played with; since 2026-10-05 a weapon's page reads its stats from
the save instead, the real ones unless the player changed them (``weapon_stats.py``).
"""
from __future__ import annotations

import logging

from ..platform.defaults import UserDefaults
from . import weapon_stats, weapon_upgrades
from .blind_screen import BlindScreen, whole

log = logging.getLogger('store')

# --------------------------------------------------------------------------- data
#: weaponType -> what the shop says and charges for it.
#:
#:   name         what the screen reader calls the weapon
#:   key          the NSUserDefaults key that means "owned"
#:   use          the key that means "equipped"; without its USE, the weapon's name in
#:                the save's stats keys (weapon_stats.py)
#:
#: 0x19318 (shotgun), 0x194da (M4A1), 0x196a8 (AK47), 0x19872 (MG80),
#: 0x19ce0 (japanese sword) and 0x19ea4 (grenade).  The original's stats for each,
#: which it spoke and never played with, went on 2026-10-05; the prices it charged
#: are weapon_stats.REAL's.
SHOP = {
    1: dict(name='Shotgun', key='SHOTGUN', use='SHOTGUNUSE'),
    2: dict(name='M4A1', key='M4', use='M4USE'),
    3: dict(name='AK47', key='AK47', use='AK47USE'),
    4: dict(name='MG80', key='MG80', use='MG80USE'),
    5: dict(name='Japanese sword', key='JAPAN', use='JAPANUSE'),
    0: dict(name='Grenade', key='GRENADECOUNT', use='GRENADEUSE'),
}


def stats_name(item):
    """The weapon's name in the save's stats keys: its ``use`` key without ``USE``."""
    return item['use'][:-len('USE')]


def load_stats(page, item):
    """Set a weapon's page, shop or inventory, to the stats the save holds with what its
    upgrade level adds: range in centimetres, and None for an ammo capacity or a price
    the weapon has none of."""
    name = stats_name(item)
    page.effetiverange = weapon_stats.upgraded(name, 'range')
    page.power = weapon_stats.upgraded(name, 'damage')
    page.price = weapon_stats.value(name, 'price')
    if name == 'GRENADE':
        page.ammocapacity = UserDefaults.standardUserDefaults().intForKey_('GRENADECOUNT')
    else:
        page.ammocapacity = weapon_stats.upgraded(name, 'ammo_capacity')


# -------------------------------------------------- upgrades, on both weapon pages
#: PORT ADDITION (2026-10-05, weapon_upgrades.py): the two rows a weapon's page gains,
#: numbered past the original's eight.
LEVEL_ROW = 9
UPGRADE_ROW = 10


def owns(app, name):
    """Whether the weapon has been bought: the grenade, the knife and the colt always."""
    slot = weapon_stats.NAMES.index(name)
    have = app.haveWeapon
    return slot < len(have) and have[slot] == '1'


def level_row_text(name):
    return 'Level, %d of %d' % (weapon_upgrades.level(name),
                                weapon_upgrades.max_level(name))


def upgrade_row_text(name):
    n = weapon_upgrades.level(name)
    if n >= weapon_upgrades.max_level(name):
        return 'Fully upgraded, Button'
    return 'Upgrade stats to level %d for %s gold, Button' % (
        n + 1, whole(weapon_upgrades.price(n + 1)))


def upgrade_action(page, item):
    """The upgrade button on a weapon's page, shop or inventory: raise the weapon one
    level, or say why not, and read the page's numbers anew."""
    name = stats_name(item)
    page.ui_select()
    result = weapon_upgrades.upgrade(name, page.app)
    if result == 'max':
        page.message = 'Fully upgraded.'
        page.say(page.message)
    elif result == 'gold':
        page.play(SOUND_GOLD_LACKING)                 # "Gold is lacking.", as buying says
        page.message = 'Gold is lacking.'
    else:
        load_stats(page, item)
        page.message = 'Upgraded to level %d.' % result
        page.say(page.message)
    return result

#: The original's recordings for what buying says; ``BlindScreen.play`` has the screen
#: reader say each one's words (``blind_screen.MESSAGE_TEXT``).
SOUND_GOLD_LACKING = 259            # 0x1bc28
SOUND_PURCHASED_ALREADY = 359       # 0x1bb80
SOUND_PURCHASE_COMPLETE = 260       # 0x1bf9c

BACK_TEXT = 'Back, Button'


def detail_row_text(page, row, name):
    """A weapon's page, shop or inventory, for the screen reader: rows 2 to 6 are its
    picture and its four numbers, each read with its label."""
    if row == 1:
        return BACK_TEXT
    if row == 2:
        return '%s, Image' % name
    if row == 3:
        if page.weaponType == 0:
            return 'Number of grenades, %s' % whole(page.ammocapacity)
        if page.ammocapacity is None:                 # the knife and the sword
            return 'Ammo capacity, none'
        return 'Ammo capacity, %s' % whole(page.ammocapacity)
    if row == 4:
        return 'Effective range, %s' % weapon_stats.range_text(page.effetiverange)
    if row == 5:
        return 'Damage, %s' % whole(page.power)
    if row == 6:
        if page.price is None:                        # the knife and the colt
            return 'Price, free'
        return 'Price, %s' % whole(page.price)
    return ''


# ------------------------------------------------------------- the front menu
class MainStoreController(BlindScreen):
    """-[mainStoreController selectTapPointSoundStart] 0x1dce4, tapCount 0x1d970.

    Six rows, and one of them cannot be reached: ``selectMenu`` is never set to 3
    anywhere in the class, so sound 236 ``Gold shop Button`` is never played even
    though ``glodShopAction:`` and its ``tbb`` case both exist.  The same shape as
    ``MainController``'s unreachable Exit - **reproduced**, the row is not offered.

    **DIVERGENCE:** rows 5 and 6 are left out too: the coin store (342,
    ``coinShopAction:`` 0x1e9f0) sold coins, and restore purchases (370,
    ``restoreAction:`` 0x1eb78) restored what had been bought.  Both were Apple in-app
    purchases, which no longer exist, and there are no recordings for selling coins for
    gold instead.  Coins are gone altogether: games are free.
    """

    #: 1 back (0x1dffa), 2 weapon shop (0x1e276), 4 inventory (0x1e33c); 3 is
    #: unreachable; 5 and 6 are left out
    ROWS = (1, 2, 4)
    TITLE_TEXT = 'Store.'
    ROW_TEXT = {1: BACK_TEXT,
                2: 'Weapon shop, Button',
                4: 'Inventory, Button'}

    #: The row the gold shop would have been, kept so the tbb below reads the way the
    #: binary's does.
    GOLD_SHOP_ROW = 3

    def activate(self):
        """0x1d9c2: 04 ... six cases, 1..6; 5, the coin store, and 6, restore
        purchases, are left out."""
        self.StopElseSpeak()
        row = self.selectMenu
        if row == 1:
            self.goBackAction_()
        elif row == 2:
            self.weaponShopAction_()
        elif row == 3:
            self.glodShopAction_()
        elif row == 4:
            self.inventoryAction_()
        return row

    # -[mainStoreController weaponShopAction:] 0x1e554
    def weaponShopAction_(self, *_):
        self.ui_select()
        self.push('store_weapons')

    # -[mainStoreController inventoryAction:] 0x1e868
    def inventoryAction_(self, *_):
        self.ui_select()
        self.push('inventory')

    # -[mainStoreController glodShopAction:] 0x1e6e0 - GoldStoreController, in-app
    # purchases.  Unreachable in the original as well; see the class docstring.
    def glodShopAction_(self, *_):
        self.ui_select()
        self.say('The gold store needs in-app purchases and is not available.')

    # -[mainStoreController itemShopAction:] 0x1e6dc..0x1e6e0 is four bytes long: it
    # returns.  There is no item shop.
    def itemShopAction_(self, *_):
        pass


# ------------------------------------------------------------ the weapon list
class StoreController(BlindScreen):
    """-[StoreController selectTapPointSoundStart] 0x14968, tapCount 0x14310.

    Nine rows in the original: back, the gold you have, the six weapons for sale, and
    the StoreKit bundle.  The weapon rows push ``DetailStoreController`` with the
    weaponType their ``ItemNAction:`` passes to ``setWeaponType:`` - 0x15a98 and its
    copies.

    **DIVERGENCE:** row 9, *Purchase all weapons* (366, ``ItemAllAction:`` 0x1647c,
    the product ``SixthSense.AllWeapon``), is left out.  It was an Apple in-app purchase,
    which no longer exists, there is no recording for a gold price, and each weapon can
    be bought on its own for gold.
    """

    #: 1 back (0x159a8), 2 the gold you have, 3 to 8 the six weapons; 9 is left out
    ROWS = (1, 2, 3, 4, 5, 6, 7, 8)
    TITLE_TEXT = 'Weapon shop.'
    ROW_TEXT = {1: BACK_TEXT,
                3: 'Shotgun, Button',
                4: 'M4A1, Button',
                5: 'AK47, Button',
                6: 'MG80, Button',
                7: 'Japanese sword, Button',
                8: 'Grenade, Button'}

    #: 0x15a90, 0x15c4c, ... - Item1..Item6Action's argument to setWeaponType:.
    ROW_WEAPON = {3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 0}

    def activate(self):
        """0x1436a: 05 38 56 5c 62 68 6e 74 7a - nine cases, 1..9; 9 is left out."""
        self.StopElseSpeak()
        row = self.selectMenu
        if row == 1:
            self.goBackAction_()
        elif row == 2:
            self.readgold()
        elif row in self.ROW_WEAPON:
            self.ItemAction_(self.ROW_WEAPON[row])
        return row

    def row_text(self, row):
        if row == 2:
            return 'Obtained gold, %s' % whole(self.app.haveGold)
        return BlindScreen.row_text(self, row)

    # -[StoreController readgold] 0x15720
    def readgold(self, *_):
        self.say(self.row_text(2))
        return self.app.haveGold

    # -[StoreController reloadGold] 0x13640 - the label, which there is none of here.
    def reloadGold(self):
        pass

    # -[StoreController Item1Action:] 0x15a14 and its five copies
    def ItemAction_(self, weapon_type):
        self.ui_select()
        self.push('store_detail', weapon_type)


# ----------------------------------------------------------- one weapon's page
class DetailStoreController(BlindScreen):
    """-[DetailStoreController selectTapPointSoundStart] 0x1ab84, tapCount 0x1a578.

    Eight rows: back, the weapon's name, then its four numbers, then Buy and Try.
    ``tapCount`` here is an if/else chain rather than a table (0x1a5d0), and it only
    answers three of them - buy, try and back.
    """

    ROWS = (1, 2, 3, 4, 5, 6, 7, 8)

    def __init__(self, weaponType=1, speech=None):
        BlindScreen.__init__(self, speech=speech)
        self.weaponType = weaponType
        self.viewDidLoad()

    # -[DetailStoreController viewDidLoad] 0x190dc
    def viewDidLoad(self):
        item = SHOP[self.weaponType]
        # 0x19ea4: the grenade's ammo capacity is GRENADECOUNT.  PORT DIVERGENCE: the
        # rest come from the save (weapon_stats.py), not the original's literals.
        load_stats(self, item)
        self.selectMenu = 1                                   # 0x19b90
        self.message = ''                                     # maskLabel

    def title_text(self):
        return '%s.' % SHOP[self.weaponType]['name']

    @property
    def stats_name(self):
        return stats_name(SHOP[self.weaponType])

    def rows(self):
        """PORT ADDITION (2026-10-05): the level after the four numbers, and once the
        weapon is bought, the upgrade button in Buy's place.  The grenade, bought again
        and again, keeps Buy and has the upgrade button after it."""
        name = self.stats_name
        if name == 'GRENADE':
            return (1, 2, 3, 4, 5, 6, LEVEL_ROW, 7, UPGRADE_ROW, 8)
        if owns(self.app, name):
            return (1, 2, 3, 4, 5, 6, LEVEL_ROW, UPGRADE_ROW, 8)
        return (1, 2, 3, 4, 5, 6, LEVEL_ROW, 7, 8)

    def row_text(self, row):
        if row == 7:
            return 'Buy, Button'
        if row == 8:
            return 'Try, Button'
        if row == LEVEL_ROW:
            return level_row_text(self.stats_name)
        if row == UPGRADE_ROW:
            return upgrade_row_text(self.stats_name)
        return detail_row_text(self, row, SHOP[self.weaponType]['name'])

    def activate(self):
        self.StopElseSpeak()
        row = self.selectMenu
        if row == 1:
            self.goBackAction_()
        elif row == 7 and row in self.rows():
            if self.buyAction_() and UPGRADE_ROW in self.rows() and 7 not in self.rows():
                self.selectMenu = UPGRADE_ROW     # Buy is gone; stand on what replaced it
        elif row == 8:
            self.testAction_()
        elif row == UPGRADE_ROW and row in self.rows():
            self.upgradeAction_()
        return row

    def upgradeAction_(self, *_):
        """PORT ADDITION: raise the weapon one level (weapon_upgrades.py)."""
        return upgrade_action(self, SHOP[self.weaponType])

    # -[DetailStoreController buyAction:] 0x1b9e4
    def buyAction_(self, *_):
        """PORT DIVERGENCE (tsatria03, 2026-10-07): Buy clicks first, ``ui_select`` as Back
        (0x1b9b4), Try (0x1c2a6) and the upgrade button do.  The original's buyAction: plays
        only its voice line, 359, 259 or 260, which the screen reader says now, so without
        the click Buy was the one silent button in the shop."""
        self.ui_select()
        item = SHOP[self.weaponType]
        d = UserDefaults.standardUserDefaults()

        if self.weaponType != 0 and d.intForKey_(item['key']) != 0:   # 0x1bb58
            self.play(SOUND_PURCHASED_ALREADY)
            self.message = 'This weapon has been purchased.'
            return False

        if self.app.haveGold < self.price:                            # 0x1bbd4
            # 0x1bbee: the original played its recording; the screen reader says it now.
            self.play(SOUND_GOLD_LACKING)
            self.message = 'Gold is lacking.'
            return False

        self.app.haveGold -= self.price                               # 0x1bd42
        d.setObject_forKey_('%d' % self.app.haveGold, 'GOLD')         # 0x1bdb8
        if self.weaponType == 0:
            # 0x1c144 `adds r3, r0, #1` - a thousand gold buys one grenade.
            count = d.intForKey_('GRENADECOUNT') + 1
            d.setObject_forKey_('%d' % count, 'GRENADECOUNT')
            self.ammocapacity = count                                 # 0x1c1b8
        else:
            d.setObject_forKey_('1', item['use'])                     # 0x1be08
            d.setObject_forKey_('1', item['key'])
        d.synchronize()
        self.play(SOUND_PURCHASE_COMPLETE)                            # 0x1bf9c
        self.message = 'Purchase has completed.'
        self.app.weaponHave()                                         # 0x1c0a8
        return True

    # -[DetailStoreController testAction:] 0x1c1c0
    def testAction_(self, *_):
        """The Try button pushes ``Stage_1_TEST``, the weapon test range, holding the
        weapon on this page (``setTestWeapon:``, 0x1c3d6; the slot for each weaponType
        is ``stage_1_test.TEST_WEAPON``).  It is the one door into the range.

        The original first refuses while VoiceOver is running, with an alert asking
        for it to be turned off (0x1c20a).  The port leaves that out: a player here
        always has a screen reader running, and the range speaks for itself."""
        from .stage_1_test import test_weapon_for
        self.StopElseSpeak()                                          # 0x1c280
        self.ui_select()                                              # 10, 0x1c2a6
        self.push('weapon_test', test_weapon_for(self.weaponType))

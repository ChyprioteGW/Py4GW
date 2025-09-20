from .enums_src.GameData_enums import (
    Ailment,
    Allegiance,
    Attribute,
    DamageType,
    DyeColor,
    Inscription,
    Profession,
    ProfessionShort,
    Range,
    Reduced_Ailment,
    SkillType,
    Weapon,
    WeaporReq,
)
from .enums_src.Hero_enums import HeroType, PetBehavior
from .enums_src.IO_enums import Key, MouseButton
from .enums_src.Item_enums import Bags, IdentifyAllType, ItemType, Rarity, SalvageAllType
from .enums_src.Map_enums import (
    explorable_name_to_id,
    explorables,
    name_to_map_id,
    outpost_name_to_id,
    outposts,
)
from .enums_src.Model_enums import AgentModelID, ModelID, PetModelID, SPIRIT_BUFF_MAP, SpiritModelID
from .enums_src.Multiboxing_enums import CombatPrepSkillsType, SharedCommandType
from .enums_src.Py4GW_enums import Console
from .enums_src.Region_enums import (
    Campaign,
    Continent,
    District,
    Language,
    RegionType,
    ServerLanguage,
    ServerLanguageName,
    ServerRegionName,
)
from .enums_src.Texture_enums import (
    ProfessionTextureMap,
    get_texture_for_item,
    get_texture_for_skill,
)
from .enums_src.Title_enums import TITLE_NAME, TitleID
from .enums_src.UI_enums import (
    ChatChannel,
    ControlAction,
    EnumPreference,
    FlagPreference,
    ImguiFonts,
    NumberPreference,
    StringPreference,
    UIMessage,
    WindowID,
)
__all__ = [
    # GameData_enums
    "Ailment",
    "Allegiance",
    "Attribute",
    "DamageType",
    "DyeColor",
    "Inscription",
    "Profession",
    "ProfessionShort",
    "Range",
    "Reduced_Ailment",
    "SkillType",
    "Weapon",
    "WeaporReq",

    # Hero_enums
    "HeroType",
    "PetBehavior",

    # IO_enums
    "Key",
    "MouseButton",

    # Item_enums
    "Bags",
    "IdentifyAllType",
    "ItemType",
    "Rarity",
    "SalvageAllType",

    # Map_enums
    "explorable_name_to_id",
    "explorables",
    "name_to_map_id",
    "outpost_name_to_id",
    "outposts",

    # Model_enums
    "AgentModelID",
    "ModelID",
    "PetModelID",
    "SPIRIT_BUFF_MAP",
    "SpiritModelID",

    # Multiboxing_enums
    "CombatPrepSkillsType",
    "SharedCommandType",

    # Py4GW_enums
    "Console",

    # Region_enums
    "Campaign",
    "Continent",
    "District",
    "Language",
    "RegionType",
    "ServerLanguage",
    "ServerLanguageName",
    "ServerRegionName",

    # Texture_enums
    "ProfessionTextureMap",
    "get_texture_for_item",
    "get_texture_for_skill",

    # Title_enums
    "TITLE_NAME",
    "TitleID",

    # UI_enums
    "ChatChannel",
    "ControlAction",
    "EnumPreference",
    "FlagPreference",
    "ImguiFonts",
    "NumberPreference",
    "StringPreference",
    "UIMessage",
    "WindowID",
]




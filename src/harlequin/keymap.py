from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from typing_extensions import NotRequired

from harlequin.exception import HarlequinConfigError

# TODO: ADD VALIDATION when creating bindings from config


class RawKeyBinding(TypedDict):
    keys: str
    action: str
    key_display: NotRequired[str]


class RawKeyMap(TypedDict):
    name: str
    bindings: list[RawKeyBinding]


@dataclass
class HarlequinKeyBinding:
    keys: str
    """Comma-separated list of virtual key names."""
    action: str
    """The name of an action. Must be a key of harlequin.actions.HARLEQUIN_ACTIONS"""
    key_display: str | None = None
    """If specified, overrides the key display in Harlequin footer for this binding."""

    def to_dict(self) -> RawKeyBinding:
        """
        Returns a dictionary that can be written to a TOML config file.
        """
        d: RawKeyBinding = {"keys": self.keys, "action": self.action}
        if self.key_display is not None:
            d["key_display"] = self.key_display
        return d


@dataclass
class HarlequinKeyMap:
    name: str
    bindings: list[HarlequinKeyBinding]

    @classmethod
    def from_config(cls, name: str, bindings: list[RawKeyBinding]) -> "HarlequinKeyMap":
        from harlequin.actions import HARLEQUIN_ACTIONS

        try:
            keymap = cls(
                name=name,
                bindings=[HarlequinKeyBinding(**binding) for binding in bindings],
            )
        except TypeError as e:
            bad_key = str(e).split("argument ")[-1].strip("'")
            raise HarlequinConfigError(
                title="Harlequin could not load your keymap.",
                msg=(
                    "Key bindings must be defined in config files with "
                    "only three properties: `keys`, `action`, and `key_display`. "
                    f"Got a binding in the map named {name} that tried to define "
                    f"a property: {bad_key!r}"
                ),
            ) from e
        for b in keymap.bindings:
            if b.action not in HARLEQUIN_ACTIONS:
                raise HarlequinConfigError(
                    title="Harlequin could not load your keymap.",
                    msg=(
                        f"Key binding in keymap {name} specifies unknown action "
                        f"{b.action!r}."
                    ),
                )
        return keymap

    def to_dict(self) -> RawKeyMap:
        return {"name": self.name, "bindings": [b.to_dict() for b in self.bindings]}

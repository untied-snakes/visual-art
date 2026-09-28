"""Finds every visual in visuals/."""
import importlib
import inspect
import pkgutil

from visual_art import visuals as visuals_package
from visual_art.visual import Visual


def find_visuals() -> dict[str, type[Visual]]:
    """Return {"bars": BarsVisual, ...} for every visuals/*.py not starting with _."""
    found = {}
    for module_info in pkgutil.iter_modules(visuals_package.__path__):
        name = module_info.name
        if name.startswith("_"):
            continue
        module = importlib.import_module(f"visual_art.visuals.{name}")
        classes = [
            obj
            for obj in vars(module).values()
            if inspect.isclass(obj)
            and issubclass(obj, Visual)
            and obj is not Visual
            and obj.__module__ == module.__name__
        ]
        if len(classes) != 1:
            raise ValueError(
                f"visuals/{name}.py must define exactly one Visual subclass, found {len(classes)}"
            )
        found[name] = classes[0]
    return dict(sorted(found.items()))

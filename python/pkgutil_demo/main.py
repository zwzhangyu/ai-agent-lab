import pkgutil
import importlib
import tools

for info in pkgutil.iter_modules(tools.__path__):
    module_name = f"tools.{info.name}"

    module = importlib.import_module(module_name)

    print("模块：", module_name)
    print(module.run("hello"))
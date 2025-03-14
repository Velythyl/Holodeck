import json
import os

from ai2thor.controller import Controller
from ai2thor.hooks.procedural_asset_hook import ProceduralAssetHookRunner
from tqdm import tqdm

from ai2holodeck.constants import THOR_COMMIT_ID, OBJATHOR_ASSETS_DIR
from hippo.hippocontainers.runtimeobjects import RuntimeObjectContainer
from hippo.hippocontainers.scenedata import HippoObject
from hippo.utils.file_utils import get_tmp_folder

def _get_self_install_dir():
    filepath = __file__
    return "/".join(filepath.split("/")[:-2])

def _get_ai2thor_install_dir():
    return _get_self_install_dir() + "/ai2thor"

def _get_ai2thor_install_build_dir():
    return _get_ai2thor_install_dir() + "/unity/builds"

def _get_ai2thorbuilds_dir(which="fixed"):
    return _get_self_install_dir() + f"/ai2thorbuilds/{which}"


def get_hippo_controller(scene, target_dir=None, objathor_asset_dir=OBJATHOR_ASSETS_DIR, get_runtime_container=False,  **kwargs):
    if isinstance(scene, str) and scene.endswith(".json"):
        with open(scene, "r") as f:
            scene = json.load(f)

    if isinstance(scene, dict):
        if scene["objects"][0]["IS_HIPPO"] is True:
            if target_dir is None:
                target_dir = get_tmp_folder()

            hippo_objects = []
            for object in tqdm(scene["objects"], desc="Concretizing objects..."):
                ho = HippoObject.from_holodeckdict(object)
                ho.concretize(target_dir, objathor_asset_dir)
                hippo_objects.append(ho)
            runtime_container = RuntimeObjectContainer.create(hippo_objects, is_ai2thor_metadata=False)
        else:
            target_dir = objathor_asset_dir
            runtime_container = None

    try:
        os.unlink(_get_ai2thor_install_build_dir())
    except:
        pass
    assert not os.path.exists(_get_ai2thor_install_build_dir())
    os.symlink(_get_ai2thorbuilds_dir(), _get_ai2thor_install_build_dir(), target_is_directory=True)

    controller = Controller(
        #commit_id=THOR_COMMIT_ID,
        #local_executable_path="../ai2thorbuilds/original/thor-Linux64-local/thor-Linux64-local",
        local_build=True,
        agentMode="default",
        makeAgentsVisible=False,
        scene=scene,
        #gridSize=0.01,
        action_hook_runner=ProceduralAssetHookRunner(
            asset_directory=target_dir,
            asset_symlink=True,
            verbose=True,
            load_file_in_unity=True
        ),
        **kwargs
    )

    if get_runtime_container:
        ai2thor_objects = controller.last_event.metadata["objects"]
        if runtime_container is None:
            runtime_container = RuntimeObjectContainer.create(ai2thor_objects, is_ai2thor_metadata=True)
        else:
            runtime_container = runtime_container.update_from_ai2thor(ai2thor_objects)
        return controller, runtime_container
    else:
        return controller

def get_hippo_controller_OLD(scene, target_dir=None, objathor_asset_dir=OBJATHOR_ASSETS_DIR, **kwargs):
    if isinstance(scene, str) and scene.endswith(".json"):
        with open(scene, "r") as f:
            scene = json.load(f)

    if target_dir is None:
        target_dir = get_tmp_folder()

    for object in tqdm(scene["objects"], desc="Concretizing objects..."):
        HippoObject.from_holodeckdict(object).concretize(target_dir, objathor_asset_dir)

    controller = Controller(
        commit_id=THOR_COMMIT_ID,
        agentMode="default",
        makeAgentsVisible=False,
        visibilityDistance=1.5,
        scene=scene,
        fieldOfView=90,
        #gridSize=0.01,
        action_hook_runner=ProceduralAssetHookRunner(
            asset_directory=target_dir,
            asset_symlink=True,
            verbose=True,
        ),
        **kwargs
    )
    return controller


if __name__ == "__main__":
    get_hippo_controller("./sampled_scenes/0/scene.json", OBJATHOR_ASSETS_DIR)
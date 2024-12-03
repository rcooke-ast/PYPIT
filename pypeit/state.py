""" States to monitor the progress of the reduction """
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal

# Hopefully this isn't circular
import io

# Calibration state
class BaseCalibState(BaseModel):
    calib_id: int # Calibration ID
    det: str      # Detector
    step: str
    input_files: Optional[List[str]] = None
    output_files: Optional[List[str]] = None
    qa_files: Optional[List[str]] = None
    status: Literal["complete", "fail", "undone"] = "undone"
    metrics: Optional[Dict[str, float]] = None

class BiasCalibState(BaseCalibState):
    step: Literal["bias"] = "bias"
    # Metrics
    mean: Optional[float] = None
    std: Optional[float] = None

class WvCalibSlit(BaseModel):
    status: Literal["complete", "fail", "undone"] = "undone"
    # Metrics
    rms: Optional[float] = None

class WvCalibState(BaseCalibState):
    step: Literal["wv_calib"] = "wv_calib"
    slits: Optional[Dict[str, WvCalibSlit]] = Field(default_factory=dict)

class RunPypeItState(BaseModel):
    pypeit_file: str
    current_step: str
    bias: Optional[List[BiasCalibState]] = Field(default_factory=list)
    wv_calib: Optional[List[WvCalibState]] = Field(default_factory=list)

    def update_calib(self, step:str, calib_id: int, det: str, key:str, value,
                     slit:str=None):
        self_items = getattr(self, step)
        # Grab the tiem
        for index, item in enumerate(self_items):
            if item.calib_id == calib_id and item.det == det:
                break
        # Set
        if slit is None:
            setattr(self_items[index], key, value)
        else:
            setattr(self_items[index].slits[slit], key, value)

    def write(self, path:str=None):
        outfile = self.pypeit_file.replace('.pypeit', '_state.json') if path is None else path
        json_string = self.model_dump_json(exclude_none=True)
        # Write
        with io.open(outfile, 'w', encoding='utf-8') as f:
            f.write(json_string)
        #with open(outfile, 'w') as f:
        #    f.write(json_string)

        

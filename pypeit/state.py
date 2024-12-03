""" States to monitor the progress of the reduction """
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal

# Hopefully this isn't circular
import io

# Calibration state
class BaseCalibState(BaseModel):
    calib_id: int # Calibration ID
    det: int | List[int]  # Detector number or mosaic tuple
    step: str
    input_files: Optional[List[str]] = None
    output_files: Optional[List[str]] = None
    qa_files: Optional[List[str]] = None
    status: Literal["complete", "fail", "undone", "running"] = "undone"
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

calib_classes = {
    'bias': BiasCalibState,
    'wv_calib': WvCalibState
}

class RunPypeItState(BaseModel):
    pypeit_file: str
    current_step: str
    previous_step: str = 'none'
    bias: Optional[List[BiasCalibState]] = Field(default_factory=list)
    wv_calib: Optional[List[WvCalibState]] = Field(default_factory=list)

    def update_calib(self, step:str, calib_id: int, det: str, key:str, value,
                     slit:str=None):
        # Current step
        if self.current_step != step:
            self.previous_step = self.current_step
        self.current_step = step
        # Select items so far
        if step not in ['bias', 'wv_calib']:
            return
        # Grab the entry
        self_items = getattr(self, step)
        found_it = False
        # Grab the tiem
        for index, item in enumerate(self_items):
            # TODO -- if det is a tuple, this will probably fail
            if item.calib_id == calib_id and item.det == det:
                found_it = True
                break
        # Create it?
        if not found_it:
            item = calib_classes[step](calib_id=calib_id, det=det)
            self_items.append(item)
            index = -1
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
        

"""
Script to run to a single calibration step for an input frame

.. include common links, assuming primary doc root is up one directory
.. include:: ../include/links.rst
"""

from pypeit.scripts import scriptbase

class RunToCalibStep(scriptbase.ScriptBase):

    # TODO: Combining classmethod and property works in python 3.9 and later
    # only: https://docs.python.org/3.9/library/functions.html#classmethod
    # Order matters.  In python 3.9, it would be:
    #
    # @classmethod
    # @property
    #
    # Because we're not requiring python 3.9 yet, we have to leave this as a
    # classmethod only:
    @classmethod
    def name(cls):
        """
        Return the name of the executable.
        """
        return 'pypeit_run_to_calibstep'

    @classmethod
    def get_parser(cls, width=None):
        import argparse

        parser = super().get_parser(description='Run PypeIt to a single calibration step for an input frame',
                                    width=width, formatter=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('pypeit_file', type=str,
                            help='PypeIt reduction file (must have .pypeit extension)')
        parser.add_argument('frame', type=str, help='Raw science frame to reduce as listed in your PypeIt file, e.g. b28.fits.gz')
        parser.add_argument('step', type=str, help='Calibration step to perform')
        #
        #parser.add_argument('--det', type=str, help='Detector to reduce')

        # TODO -- Grab these from run_pypeit.py ?
        parser.add_argument('-v', '--verbosity', type=int, default=2,
                            help='Verbosity level between 0 [none] and 2 [all]')

        parser.add_argument('-r', '--redux_path', default=None,
                            help='Path to directory for the reduction.  Only advised for testing')
        parser.add_argument('-s', '--show', default=False, action='store_true',
                            help='Show reduction steps via plots (which will block further '
                                 'execution until clicked on) and outputs to ginga. Requires '
                                 'remote control ginga session via '
                                 '"ginga --modules=RC,SlitWavelength &"')

        return parser

    @staticmethod
    def main(args):

        import os
        import numpy as np
        from IPython import embed

        from pypeit import pypeit
        from pypeit import msgs

        # Load options from command line
        splitnm = os.path.splitext(args.pypeit_file)
        if splitnm[1] != '.pypeit':
            msgs.error('Input file must have a .pypeit extension!')
        logname = splitnm[0] + ".log"

        # Instantiate the main pipeline reduction object
        pypeIt = pypeit.PypeIt(args.pypeit_file, verbosity=args.verbosity,
                               redux_path=args.redux_path, 
                               logname=logname, show=args.show)
        pypeIt.reuse_calibs = True

        # Find the detectors to reduce
        detectors = pypeIt.select_detectors(
            pypeIt.spectrograph, pypeIt.par['rdx']['detnum'],
            slitspatnum=pypeIt.par['rdx']['slitspatnum'])
        #if args.det is not None:
        #    embed(header='Check detectors and deal!')

        # Find the row of the frame
        row = np.where(pypeIt.fitstbl['filename'] == args.frame)[0]
        if len(row) != 1:
            msgs.error(f"Frame {args.frame} not found or not unique")
        row = int(row)

        # Calibrations?
        for det in detectors:
            pypeIt.calib_one([row], det, stop_at_step=args.step)
        
        # QA HTML
        msgs.info('Generating QA HTML')
        pypeIt.build_qa()
        msgs.close()

        return 0


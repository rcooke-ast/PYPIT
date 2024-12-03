"""
Script to run to a single calibration step for an input frame

.. include common links, assuming primary doc root is up one directory
.. include:: ../include/links.rst
"""

from pypeit.scripts import scriptbase

class RunAStep(scriptbase.ScriptBase):

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
        return 'run_to_calibstep'

    @classmethod
    def usage(cls):
        """
        Print pypeit usage description.
        """
        import textwrap
        import pypeit
        from pypeit.spectrographs import available_spectrographs

        spclist = ', '.join(available_spectrographs)
        spcl = textwrap.wrap(spclist, width=70)
        descs = '##  '
        descs += '\x1B[1;37;42m' + 'PypeIt : '
        descs += 'The Python Spectroscopic Data Reduction Pipeline v{0:s}'.format(pypeit.__version__) \
                  + '\x1B[' + '0m' + '\n'
        descs += '##  '
        descs += '\n##  Available spectrographs include:'
        for ispcl in spcl:
            descs += '\n##   ' + ispcl
        return descs

    @classmethod
    def get_parser(cls, width=None):
        import argparse

        parser = super().get_parser(description=cls.usage(),
                                    width=width, formatter=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('pypeit_file', type=str,
                            help='PypeIt reduction file (must have .pypeit extension)')
        parser.add_argument('frame', type=str, help='Frame to reduce')
        parser.add_argument('step', type=str, help='Step to perform')
        #
        parser.add_argument('--det', type=str, help='Detector to reduce')

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
        if args.det is not None:
            embed(header='Check detectors and deal!')

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


# TODO -- Remove these lines
if __name__ == '__main__':
    s = RunAStep()
    s.main(s.parse_args())



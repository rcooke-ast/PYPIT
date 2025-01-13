"""
Module for DK1.54m DFOSC spectrograph

.. include:: ../include/links.rst
"""
from IPython import embed

import numpy as np

from astropy.time import Time

from pypeit import msgs
from pypeit import telescopes
from pypeit.core import framematch
from pypeit.spectrographs import spectrograph
from pypeit.core import parse
from pypeit.images import detector_container


class DFOSCSpectrograph(spectrograph.Spectrograph):
    """
    Child to handle NOT DFOSC spectrograph
    """
    ndet = 1
    name = 'd154_dfosc'
    telescope = telescopes.D154TelescopePar()
    camera = 'DFOSC'
    url = 'https://www.eso.org/public/teles-instr/lasilla/danish154/dfosc/'
    header_name = 'DFOSC_FASU'
    pypeline = 'MultiSlit'
    supported = True
    comment = 'For horizontal slits only. Grisms 3, 5, 7, 9, 10, 11, 13, 14, 15, 16 for DFOSC'

    def get_detector_par(self, det, hdu=None):
        """
        Return metadata for the selected detector.

        Detector data from `here
        <http://www.not.iac.es/instruments/detectors/CCD14/>`__.

        .. warning::

            Many of the necessary detector parameters are read from the file
            header, meaning the ``hdu`` argument is effectively **required**.  
            The optional use of ``hdu`` is only viable for
            automatically generated documentation.

        Args:
            det (:obj:`int`):
                1-indexed detector number.
            hdu (`astropy.io.fits.HDUList`_, optional):
                The open fits file with the raw image of interest.  If not
                provided, frame-dependent parameters are set to a default.

        Returns:
            :class:`~pypeit.images.detector_container.DetectorContainer`:
            Object with the detector metadata.
        """
        # http://www.not.iac.es/instruments/detectors/CCD14/
        # Actual detecor used is CCD3

        if hdu is None:
            binning = '1,1'
            gain = None
            ronoise = None
        else:
            binning = self.get_meta_value(self.get_headarr(hdu), 'binning')
            #gain = np.atleast_1d(hdu[1].header['GAIN'])  # e-/ADU
            #ronoise = np.atleast_1d(hdu[1].header['RDNOISE'])  # e-

        # Detector 1 
        # TODO: flip axis? dfosc uses vertical slits
        detector_dict = dict(
            binning         = binning,
            det             = 1,
            dataext         = 0,
            specaxis        = 0,
            specflip        = True,
            spatflip        = False,
            xgap            = 0.,
            ygap            = 0.,
            ysize           = 1.,
            platescale      = 0.29,
            mincounts       = -1e10,
            darkcurr        = 1.3,      # e-/pix/hr
            saturation      = 700000.,  # ADU
            nonlinear       = 0.86,
            datasec         = np.atleast_1d('[:,{}:{}]'.format(1, 2148)),  # Unbinned
            oscansec        = None,
            numamplifiers   = 1,
            gain            = np.atleast_1d(0.164),     # e-/ADU   This is not the correct value, test, and update with flats
            ronoise         = np.atleast_1d(9.1)   # e-
        )

#        # Parse datasec, oscancsec from the header
#        head1 = hdu[1].header
#        detector_dict['gain'] = np.atleast_1d(head1['GAIN'])  # e-/ADU
#        detector_dict['ronoise'] = np.atleast_1d(head1['RDNOISE'])  # e-

        # Return
        return detector_container.DetectorContainer(**detector_dict)

    @classmethod
    def default_pypeit_par(cls):
        """
        Return the default parameters to use for this instrument.

        Returns:
            :class:`~pypeit.par.pypeitpar.PypeItPar`: Parameters required by
            all of PypeIt methods.
        """
        par = super().default_pypeit_par()

        # Ignore PCA
        par['rdx']['ignore_bad_headers'] = True
        #par['baseprocess']['use_pixelflat'] = False
        #par['baseprocess']['use_illumflat'] = False
        par['calibrations']['pixelflatframe']['process']['use_pixelflat'] = False
        par['calibrations']['illumflatframe']['process']['use_illumflat'] = False 
        par['calibrations']['slitedges']['sync_predict'] = 'nearest'
        par['calibrations']['slitedges']['bound_detector'] = True
        par['calibrations']['slitedges']['edge_thresh'] = 20.0
        par['calibrations']['slitedges']['fit_min_spec_length'] = 0.4

        # Tilt parameters
        #par['calibrations']['tilts']['tracethresh'] = 3.0
        #par['calibrations']['tilts']['spat_order'] = 2
        #par['calibrations']['tilts']['spec_order'] = 3
        
        # Image processing
        #par['scienceframe']['process']['use_overscan'] = False 

        # 1D wavelength solution
        par['calibrations']['wavelengths']['method'] = 'full_template'
        par['calibrations']['wavelengths']['lamps'] = ['HgI_DFOSC']
        #par['calibrations']['wavelengths']['rms_thresh_frac_fwhm'] = 1.0
        #par['calibrations']['wavelengths']['sigdetect'] = 1.0
        par['calibrations']['wavelengths']['fwhm'] = 12.0
        par['calibrations']['wavelengths']['n_final'] = 5
        #par['calibrations']['wavelengths']['cc_thresh'] = ['0.5']

        # Flats
        #par['calibrations']['flatfield']['tweak_slits_thresh'] = 1.5
        #par['calibrations']['flatfield']['tweak_slits_maxfrac'] = 1.0
        par['calibrations']['flatfield']['slit_illum_finecorr'] = False
        par['calibrations']['flatfield']['tweak_slits'] = False
        par['calibrations']['flatfield']['saturated_slits'] = 'continue'
        par['calibrations']['flatfield']['method'] = 'skip'
        
        # Extraction
        par['reduce']['skysub']['bspline_spacing'] = 0.8
        par['reduce']['skysub']['no_poly'] = True
        par['reduce']['skysub']['bspline_spacing'] = 0.6
        par['reduce']['skysub']['joint_fit'] = False
        par['reduce']['skysub']['global_sky_std']  = False

        par['reduce']['extraction']['sn_gauss'] = 4.0
        par['reduce']['skysub']['sky_sigrej'] = 5.0

        # No overscan region!
        turn_off = dict(use_overscan=False)
        par.reset_all_processimages_par(**turn_off)

        return par

    def init_meta(self):
        """
        Define how metadata are derived from the spectrograph files.

        That is, this associates the PypeIt-specific metadata keywords
        with the instrument-specific header cards using :attr:`meta`.
        """
        self.meta = {}
        # Required (core)
        self.meta['ra'] = dict(ext=0, card='OBJRA')
        #self.meta['ra'] = dict(ext=0, card='RA')
        #self.meta['ra'] = dict(card=None, compound=True)
        self.meta['dec'] = dict(ext=0, card='OBJDEC')
        #self.meta['dec'] = dict(ext=0, card='DEC')
        self.meta['target'] = dict(ext=0, card='OBJECT')
        self.meta['decker'] = dict(ext=0, card='DFAPRTNM')
        self.meta['binning'] = dict(card=None, compound=True)

        self.meta['mjd'] = dict(ext=0, card=None, compound=True)
        #self.meta['mjd'] = dict(ext=0, card='DATE-OBS')
        self.meta['exptime'] = dict(ext=0, card='EXPTIME')
        self.meta['airmass'] = dict(ext=0, card='AIRMASS')
        # Extras for config and frametyping
        self.meta['dispname'] = dict(ext=0, card='DFGRNM')
        self.meta['idname'] = dict(ext=0, card='IMAGETYP')
        self.meta['instrument'] = dict(ext=0, card='INSTRUME')

    def compound_meta(self, headarr, meta_key):
        """
        Methods to generate metadata requiring interpretation of the header
        data, instead of simply reading the value of a header card.

        Args:
            headarr (:obj:`list`):
                List of `astropy.io.fits.Header`_ objects.
            meta_key (:obj:`str`):
                Metadata keyword to construct.

        Returns:
            object: Metadata value read from the header(s).
        """
        if meta_key == 'binning':
            # PypeIt frame
            binspatial = headarr[0]['BINX']
            binspec = headarr[0]['BINY']
            return parse.binning2string(binspec, binspatial)
        elif meta_key == 'mjd':
            time = headarr[0]['DATE-OBS']
            ttime = Time(time, format='isot')
            return ttime.mjd
        elif meta_key == 'ra':
            objra = headarr[0]['OBJRA'] # Given in hours, not deg
            return objra*15.
        msgs.error("Not ready for this compound meta")

    def configuration_keys(self):
        """
        Return the metadata keys that define a unique instrument
        configuration.

        This list is used by :class:`~pypeit.metadata.PypeItMetaData` to
        identify the unique configurations among the list of frames read
        for a given reduction.

        Returns:
            :obj:`list`: List of keywords of data pulled from file headers
            and used to constuct the :class:`~pypeit.metadata.PypeItMetaData`
            object.
        """
        return ['dispname', 'decker', 'binning']

    def raw_header_cards(self):
        """
        Return additional raw header cards to be propagated in
        downstream output files for configuration identification.

        The list of raw data FITS keywords should be those used to populate
        the :meth:`~pypeit.spectrographs.spectrograph.Spectrograph.configuration_keys`
        or are used in :meth:`~pypeit.spectrographs.spectrograph.Spectrograph.config_specific_par`
        for a particular spectrograph, if different from the name of the
        PypeIt metadata keyword.

        This list is used by :meth:`~pypeit.spectrographs.spectrograph.Spectrograph.subheader_for_spec`
        to include additional FITS keywords in downstream output files.

        Returns:
            :obj:`list`: List of keywords from the raw data files that should
            be propagated in output files.
        """
        return ['DFGRNM', 'DFAPRTNM', 'BINX', 'BINY']

    def check_frame_type(self, ftype, fitstbl, exprng=None):
        """
        Check for frames of the provided type.

        Args:
            ftype (:obj:`str`):
                Type of frame to check. Must be a valid frame type; see
                frame-type :ref:`frame_type_defs`.
            fitstbl (`astropy.table.Table`_):
                The table with the metadata for one or more frames to check.
            exprng (:obj:`list`, optional):
                Range in the allowed exposure time for a frame of type
                ``ftype``. See
                :func:`pypeit.core.framematch.check_frame_exptime`.

        Returns:
            `numpy.ndarray`_: Boolean array with the flags selecting the
            exposures in ``fitstbl`` that are ``ftype`` type frames.
        """
        good_exp = framematch.check_frame_exptime(fitstbl['exptime'], exprng)
        if ftype == 'science':
            return good_exp & (fitstbl['idname'] == 'OBJECT')
        if ftype == 'standard':
            return good_exp & (fitstbl['idname'] == 'STAND')
                               #| (fitstbl['target'] == 'STD') | (fitstbl['target'] == 'STD,SLIT'))
        if ftype == 'bias':
            return good_exp & (fitstbl['idname'] == 'BIAS')
        if ftype in ['pixelflat', 'trace', 'illumflat']:
            return good_exp & (fitstbl['idname'] == 'FLAT,SKY')
            #return good_exp & (fitstbl['idname'] == 'FLAT,LAMP')
        if ftype in ['dark']:
            return good_exp & (fitstbl['idname']=='DARK')
        if ftype in ['arc','tilt']:
            return good_exp & (fitstbl['idname'] == 'WAVE,LAMP')
        msgs.warn('Cannot determine if frames are of type {0}.'.format(ftype))
        return np.zeros(len(fitstbl), dtype=bool)

    def config_specific_par(self, scifile, inp_par=None):
        """
        Modify the PypeIt parameters to hard-wired values used for
        specific instrument configurations.

        Args:
            scifile (:obj:`str`):
                File to use when determining the configuration and how
                to adjust the input parameters.
            inp_par (:class:`~pypeit.par.parset.ParSet`, optional):
                Parameter set used for the full run of PypeIt.  If None,
                use :func:`default_pypeit_par`.

        Returns:
            :class:`~pypeit.par.parset.ParSet`: The PypeIt parameter set
            adjusted for configuration specific parameter values.
        """
        # Start with instrument wide
        par = super().config_specific_par(scifile, inp_par=inp_par)

        # Wavelength calibrations
        if self.get_meta_value(scifile, 'dispname') == 'Grism_#3':
            par['calibrations']['wavelengths']['reid_arxiv'] = 'd154_dfosc_grism3.fits'
        #elif self.get_meta_value(scifile, 'dispname') == 'Grism_#4':
        #    par['calibrations']['wavelengths']['reid_arxiv'] = 'not_alfosc_grism4.fits'
        #    par['calibrations']['wavelengths']['lamps'] = ['HgI']
        elif self.get_meta_value(scifile, 'dispname') == 'Grism_#5':
            par['calibrations']['wavelengths']['reid_arxiv'] = 'd154_dfosc_grism5.fits'
        elif self.get_meta_value(scifile, 'dispname') == 'Grism_#6':
            par['calibrations']['wavelengths']['reid_arxiv'] = 'd154_dfosc_grism6.fits'
        elif self.get_meta_value(scifile, 'dispname') == 'Grism_#7':
            par['calibrations']['wavelengths']['reid_arxiv'] = 'd154_dfosc_grism7.fits'
        elif self.get_meta_value(scifile, 'dispname') == 'Grism_#8':
            par['calibrations']['wavelengths']['reid_arxiv'] = 'd154_dfosc_grism8.fits'
        elif self.get_meta_value(scifile, 'dispname') == 'Grism_#14':
            par['calibrations']['wavelengths']['reid_arxiv'] = 'd154_dfosc_grism14.fits'
        elif self.get_meta_value(scifile, 'dispname') == 'Grism_#15':
            par['calibrations']['wavelengths']['reid_arxiv'] = 'wvarxiv_d154_dfosc_vert_20250113T1459.fits'
        else:
            msgs.warn('d154_dfosc.py: YOU NEED TO ADD IN THE WAVELENGTH SOLUTION FOR THIS GRISM')

        # Return
        return par




class DFOSCSpectrographVert(DFOSCSpectrograph):
    """
    Child to handle Vertical slits for d154 DFOSC spectrograph
    """
    name = 'd154_dfosc_vert'
    comment = 'Grisms 3, 5, 6, 7, 8, 14, 15. For vertical slits only'

    def get_detector_par(self, det, hdu=None):
        """
        Return metadata for the selected detector.

        Detector data from `here
        <http://www.not.iac.es/instruments/detectors/CCD14/>`__.

        .. warning::

            Many of the necessary detector parameters are read from the file
            header, meaning the ``hdu`` argument is effectively **required** for
            DFOSC.  The optional use of ``hdu`` is only viable for
            automatically generated documentation.

        Args:
            det (:obj:`int`):
                1-indexed detector number.
            hdu (`astropy.io.fits.HDUList`_, optional):
                The open fits file with the raw image of interest.  If not
                provided, frame-dependent parameters are set to a default.

        Returns:
            :class:`~pypeit.images.detector_container.DetectorContainer`:
            Object with the detector metadata.
        """
        # http://www.not.iac.es/instruments/detectors/CCD14/  should be CCD3

        if hdu is None:
            binning = '1,1'
            gain = None
            ronoise = None
        else:
            binning = self.get_meta_value(self.get_headarr(hdu), 'binning')
            #gain = np.atleast_1d(hdu[1].header['GAIN'])  # e-/ADU
            #ronoise = np.atleast_1d(hdu[1].header['RDNOISE'])  # e-
            gain = np.atleast_1d(0.164)  # e-/ADU
            ronoise = np.atleast_1d(9.1)

        # Detector 1
        detector_dict = dict(
            binning         = binning,
            det             = 1,
            dataext         = 0,  #changed from 1 to 0 b/c of header extension
            specaxis        = 1, #Vertical slits have horizontal spectral dispersion
            specflip        = False,
            spatflip        = False,
            xgap            = 0.,
            ygap            = 0.,
            ysize           = 1.,
            platescale      = 0.29,
            mincounts       = -1e10,
            darkcurr        = 1.3,      # e-/pix/hr
            saturation      = 700000.,  # ADU
            nonlinear       = 0.86,
            datasec         = np.atleast_1d('[{}:{},:]'.format(1, 2064)),  # Unbinned
            oscansec        = None,
            numamplifiers   = 1,
            gain            = gain,     # e-/ADU
            ronoise         = ronoise   # e-
        )

        # Return
        return detector_container.DetectorContainer(**detector_dict)
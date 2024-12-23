"""
Provides a class that handles archived sensfunc files.

.. include common links, assuming primary doc root is up one directory
.. include:: ../include/links.rst
"""
from abc import ABC, abstractmethod
import os

from astropy.io import fits

from pypeit import msgs
from pypeit import dataPaths
from pypeit.sensfunc import SensFunc

class SensFileArchive(ABC):
    """Class for managing archived SensFunc files. This is an abstract class that instantitates 
    child classes based on spectrograph.
    """

    @abstractmethod
    def get_archived_sensfile(self, fitsfile):
        """Get the full path name of the archived sens file that can be used to flux calibrate a given fitsfile
        
        Args:
            fitsfile (str): The fitsfile to find an archived SensFunc file for.

        Return:
            str: The full pathname of the archived SensFunc.

        Raises:
            PypeItError: Raised an archived SensFunc file can't be found for the given fits file.
        """
        pass

    @classmethod
    def get_instance(cls, spectrograph_name):
        """Return a SensFuncArchive instance that will find archived SensFuncs for a specific spectrograph.
        
        Args:
            spectrograph_name (str): 
                The spectrograph name for the SensFuncArchive instance to return.

        Return:
            pypeit.sensfilearchive.SensFileArchive: 
                A SensFuncArchive object to find archived sensfuncs for a specific spectrograph.

        Raises:
            ValueError: Raised if the passed in spectrograph is not supported.
        """

        for child in cls.__subclasses__():
            if child.spec_name == spectrograph_name:
                return child()

        raise ValueError(f"No SensFileArchive found for {spectrograph_name}")

    @classmethod
    def supported_spectrographs(cls):
        """Return which spectrograph names support Archived SensFuncs.
        
        Return: list of str
        """
        return [child.spec_name for child in cls.__subclasses__()]


class DEIMOSSensFileArchive(SensFileArchive):
    """SensFileArchive subclass specifically for keck_deimos SensFuncs."""
    spec_name = "keck_deimos"

    def get_archived_sensfile(self, fitsfile, symlink_in_pkgdir=False):
        """Get the full path name of the archived sens file that can be used to flux calibrate a given fitsfile
        
        Args:
            fitsfile (str): The fitsfile to find an archived SensFunc file for.
            symlink_in_pkgdir (bool): Create a symlink to the the cached file in the package directory (default False)

        Return:
            str: The full pathname of the archived SensFunc.

        Raises:
            PypeItError: Raised an archived SensFunc file can't be found for the given fits file.
        """
        header = fits.getheader(fitsfile)
        
        grating = header['DISPNAME']
        if grating not in ["600ZD", "830G", "900ZD", "1200B", "1200G"]:
            msgs.error(f"There are no archived SensFuncFiles for keck_deimos grating {grating}.")

        to_pkg = 'symlink' if symlink_in_pkgdir else None
        archived_file = dataPaths.sensfunc.get_file_path(f"keck_deimos_{grating}_sensfunc.fits",
                                                         to_pkg=to_pkg)
        msgs.info(f"Found archived sensfile '{archived_file}'")
        return archived_file

    class HIRESSensFileArchive(SensFileArchive):
        """SensFileArchive subclass specifically for keck_deimos SensFuncs."""
        spec_name = "keck_hires"

        def get_archived_sensfile(self, fitsfile, symlink_in_pkgdir=False):
            """Get the full path name of the archived sens file that can be used to flux calibrate a given fitsfile

            Args:
                fitsfile (str): The fitsfile to find an archived SensFunc file for.
                symlink_in_pkgdir (bool): Create a symlink to the the cached file in the package directory (default False)

            Return:
                str: The full pathname of the archived SensFunc.

            Raises:
                PypeItError: Raised an archived SensFunc file can't be found for the given fits file.
            """
            hdu = fits.open(fitsfile)
            # get echelle orders in this spec1d file
            orders = [h.header['HIERARCH ECH_ORDER'] for h in hdu if h.name.startswith('OBJ')]
            archived_file = '/Users/dpelliccia/Desktop/adap2020/test_code/sens_keck_hires_RED_orders_93-35_sensfunc.fits'
            sensobjs = SensFunc.from_file(archived_file, chk_version=False)
            arx_orders = sensobjs.sens['ECH_ORDERS']
            # check if all orders in the spec1d file are in the archived file
            if not set(orders).issubset(set(arx_orders)):
                msgs.warn("Not all echelle orders in the spec1d file are in the archived sensfunc file. The following "
                          "orders will not be flux calib: {0}".format(set(orders) - set(arx_orders)))

            # to_pkg = 'symlink' if symlink_in_pkgdir else None
            # archived_file = dataPaths.sensfunc.get_file_path(f"keck_deimos_{grating}_sensfunc.fits",
            #                                                  to_pkg=to_pkg)
            msgs.info(f"Found archived sensfile '{archived_file}'")
            return archived_file


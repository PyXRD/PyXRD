# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

from pyxrd.generic.io.file_parsers import BaseParser, register_parser
from pyxrd.generic.io.utils import get_case_insensitive_glob

from .xml_parser_mixin import XMLParserMixin
from .xrd_parser_mixin import XRDParserMixin
from zipfile import ZipFile
import os
from pyxrd.generic.utils import not_none

@register_parser()
class BrkBRMLParser(XRDParserMixin, XMLParserMixin, BaseParser):
    """
        Bruker *.BRML format parser
    """

    description = "Bruker BRML files *.BRML"
    namespace = "xrd"
    extensions = get_case_insensitive_glob("*.BRML")
    mimetypes = ["application/zip", ]

    __file_mode__ = "r"

    @classmethod
    def _get_file(cls, filename, f=None, close=None):
        """
            Returns a three-tuple:
            filename, zipfile-object, close
        """
        if hasattr(f, "read"):
            if not isinstance(f, ZipFile):
                return filename, ZipFile(f, cls.__file_mode__), False if close == None else close
            else:
                return filename, f, False if close == None else close
        elif type(filename) is str:
            return filename, ZipFile(filename, cls.__file_mode__), True if close == None else close
        else:
            raise TypeError, "Wrong argument: either a file object or a valid \
                filename must be passed, not '%s' or '%s'" % (cls.description, filename, f)

    @classmethod
    def _get_raw_data_files(cls, f, folder):
        """
            Processes DataContainer.xml and returns a list of xml raw data
            filepaths and the sample name
        """
        with f.open("%s/DataContainer.xml" % folder) as contf:
            _, root = cls.get_xml_for_file(contf)
            sample_name = root.find("./MeasurementInfo").get("SampleName")

            raw_data_files = []
            for child in root.find("./RawDataReferenceList"):
                raw_data_files.append(child.text)

        return raw_data_files, sample_name

    @classmethod
    def _get_header_dict(cls, f, folder):
        header_d = {}
        with f.open("%s/MeasurementContainer.xml" % folder) as contf:
            _, root = cls.get_xml_for_file(contf)

            path = "./HardwareLogicExt/Instrument/" + \
                   "BeamPathContainers/BeamPathContainerAbc/BankPositions/" + \
                   "BankPosition/MountedComponent/MountedTube/%s"
            get_val = lambda label: root.find(path % label).get("Value")

            header_d.update(
                alpha1=float(get_val("WaveLengthAlpha1")),
                alpha2=float(get_val("WaveLengthAlpha2")),
                alpha_average=float(get_val("WaveLengthAverage")),
                beta=float(get_val("WaveLengthBeta")),
                alpha_factor=float(get_val("WaveLengthRatio")),
                target_type=get_val("TubeMaterial")
                #TODO fetch slits, ...
            )

        return header_d

    @classmethod
    def parse(cls, filename, f=None, data_objects=None, close=False):
        filename, f, close = cls._get_file(filename, f=f, close=close)

        num_samples = 0

        zipinfos = f.infolist()

        processed_folders = []

        data_objects = not_none(data_objects, [])

        for zipinfo in zipinfos:
            if zipinfo.filename.count('/') == 1 and "DataContainer.xml" in zipinfo.filename:

                folder = os.path.dirname(zipinfo.filename)
                if not folder in processed_folders:

                    processed_folders.append(folder)

                    raw_data_files, sample_name = cls._get_raw_data_files(f, folder)
                    header_d = cls._get_header_dict(f, folder)

                    for raw_data_filename in raw_data_files:
                        with f.open(raw_data_filename) as contf:
                            _, root = cls.get_xml_for_file(contf)

                            for route in root.findall("./DataRoutes/DataRoute"):

                                # Adapt XRDFile list & get last addition:
                                data_objects = cls._adapt_data_object_list(
                                    data_objects,
                                    num_samples=(num_samples + 1),
                                    only_extend=True
                                )
                                data_object = data_objects[num_samples]

                                # Get the Datum tags:
                                datums = route.findall("Datum")
                                data = []

                                # Parse the RawDataView tags to find out what index in
                                # the datum is used for what type of data:
                                enabled_datum_index = None
                                twotheta_datum_index = None
                                intensity_datum_index = None
                                steptime_datum_index = None
                                for dataview in route.findall("./DataViews/RawDataView"):
                                    index = int(dataview.get("Start", 0))
                                    name = dataview.get("LogicName", default="Undefined")
                                    xsi_type = dataview.get("{http://www.w3.org/2001/XMLSchema-instance}type", default="Undefined")
                                    if name == "MeasuredTime":
                                        steptime_datum_index = index
                                    elif name == "AbsorptionFactor":
                                        enabled_datum_index = index
                                    elif name == "Undefined" and xsi_type == "VaryingRawDataView":
                                        for i, definition in enumerate(dataview.findall("./Varying/FieldDefinitions")):
                                            if definition.get("TwoTheta"):
                                                index += i
                                                break
                                        twotheta_datum_index = index
                                    elif name == "Undefined" and xsi_type == "RecordedRawDataView":
                                        intensity_datum_index = index

                                # Parse the SubScanInfo list (usually only one), and
                                # then parse the datums accordingly
                                twotheta_min = None
                                twotheta_max = None
                                twotheta_count = 0
                                for subscan in route.findall("./SubScans/SubScanInfo"):
                                    # Get the steps, where to start and the planned
                                    # time per step (measuredTimePerStep deviates
                                    # if the recording was interrupted):
                                    steps = int(subscan.get("MeasuredSteps"))
                                    start = int(subscan.get("StartStepNo"))
                                    steptime = float(subscan.get("PlannedTimePerStep"))

                                    for datum in datums[start:start + steps]:
                                        values = datum.text.split(",")
                                        if values[enabled_datum_index] == "1":
                                            # Fetch values from the list:
                                            datum_steptime = float(values[steptime_datum_index])
                                            intensity = float(values[intensity_datum_index])
                                            intensity /= float(steptime * datum_steptime)
                                            twotheta = float(values[twotheta_datum_index])

                                            # Keep track of min 2theta:
                                            if twotheta_min is None:
                                                twotheta_min = twotheta
                                            else:
                                                twotheta_min = min(twotheta_min, twotheta)

                                            # Keep track of max 2theta:
                                            if twotheta_max is None:
                                                twotheta_max = twotheta
                                            else:
                                                twotheta_max = min(twotheta_max, twotheta)

                                            # Append point and increase count:
                                            data.append([twotheta, intensity])
                                            twotheta_count += 1

                                #Update header:
                                data_object.update(
                                    filename=os.path.basename(filename),
                                    name=sample_name,
                                    time_step=1, # we converted to CPS
                                    twotheta_min=twotheta_min,
                                    twotheta_max=twotheta_max,
                                    twotheta_count=twotheta_count,
                                    **header_d
                                )

                                data_object.data = data

                                num_samples += 1

                            #end for
                        #end with
                    #end for
                #end if
            #end if
        #end for

        if close: f.close()
        return data_objects

    pass # end of class

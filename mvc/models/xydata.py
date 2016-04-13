
import logging
logger = logging.getLogger(__name__)

import types, json
import numpy as np

from ..support.utils import pop_kwargs

from .base import Model
from .prop_intel import PropIntel

class XYData(Model):
    """
        An XYData is a mixin model holding a list of x-y numbers.  
        Its values can be indexed, e.g.:
         >>> xydata = XYData(data=([1, 2, 3], [[4, 5], [6, 7], [8, 9]]))
         >>> xydata[0]
         (1, [4, 5])
         
        and iterated:
         >>> xydata = XYData(data=([1, 2, 3], [[4, 5], [6, 7], [8, 9]]))
         >>> for row in xydata:
         ...  print row
         ...
         (1, [4, 5])
         (2, [6, 7])
         (3, [8, 9])
         
        You can also associate names with each column:
         >>> xydata = XYData(data=([1, 2, 3], [[4, 5], [6, 7], [8, 9]]))
         >>> xydata.y_names = ["First Column", "Second Column"]
         >>> xydata.y_names.get(0, "")
         'First Column'
    """
    # MODEL INTEL:
    class Meta(Model.Meta):
        properties = [
            PropIntel(name="data_x", data_type=object),
            PropIntel(name="data_y", data_type=object),
        ]

    # OBSERVABLE PROPERTIES:
    _data_x = None
    def get_data_x(self): return self._data_x
    def set_data_x(self, value):
        self.set_data(value, self._data_y)
    _data_y = None
    def get_data_y(self): return self._data_y
    def set_data_y(self, value):
        self.set_data(self._data_x, value)

    # REGULAR PROPERTIES:
    _y_names = []
    @property
    def y_names(self):
        if len(self) < len(self._y_names):
            return self._y_names[:len(self)]
        else:
            return self._y_names
    @y_names.setter
    def y_names(self, names):
        self._y_names = names if names is not None else []

    @property
    def size(self):
        return len(self)

    @property
    def num_columns(self):
        return 1 + self.data_y.shape[1]

    @property
    def max_y(self):
        if len(self.data_x) > 1:
            return np.max(self.data_y)
        else:
            return 0

    @property
    def min_y(self):
        if len(self.data_x) > 1:
            return np.min(self.data_y)
        else:
            return 0

    @property
    def abs_max_y(self):
        if len(self.data_x) > 1:
            return np.max(np.absolute(self.data_y))
        else:
            return 0

    @property
    def abs_min_y(self):
        if len(self.data_x) > 1:
            return np.min(np.absolute(self.data_y))
        else:
            return 0

    # ------------------------------------------------------------
    #      Initialization and other internals
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
            Valid keyword arguments for an XYData are:
                data: the actual data containing x and y values, this can be a:
                 - JSON string: "[[x1, x2, ..., xn], [y11, y21, ..., yn1], ..., [y1m, y2m, ..., ynm]]"
                 - A dictionary from a (deprecated) XYObjectListStore, containing
                   a data property, which contains a JSON string as above.
                 - A 2D-numpy array, in which its first axes contains the 
                   data rows, and its second axes contains the columns, first 
                   column being the x-data, and following columns the y-data, e.g.:
                    np.array([[x1,y11,...,y1m],
                              [x2,y21,...,y2m],
                              ...,
                              [xn,yn1,...,ynm]])
                  - An iterable containing the x-data and y-data as if it would be
                    passed to set_data(*data), e.g.:
                     ([1, 2, 3], [[4, 5], [6, 7], [8, 9]])
                names: names for the y columns (optional)
        """

        XYData.set_data(self, np.array([], dtype=float), np.zeros(shape=(0, 0), dtype=float))

        my_kwargs = pop_kwargs(kwargs,
            "names", "data",
            *[names[0] for names in type(self).Meta.get_local_storable_properties()]
        )
        super(XYData, self).__init__(*args, **kwargs)
        kwargs = my_kwargs

        self.y_names = kwargs.get("names", self.y_names)

        data = kwargs.get("data", None)
        if data is not None:
            if type(data) in types.StringTypes:
                XYData._set_from_serial_data(self, data)
            elif type(data) is types.DictionaryType:
                XYData._set_from_serial_data(self, data["properties"]["data"])
            elif isinstance(data, np.ndarray):
                XYData.set_data(self, data[:, 0], data[:, 1:])
            elif hasattr(data, '__iter__'):
                XYData.set_data(self, *data)

    # ------------------------------------------------------------
    #      Input/Output stuff
    # ------------------------------------------------------------

    def _serialize_data(self):
        """
            Internal method, should normally not be used!
            If you want to write data to a file, use the save_data method instead!
        """
        conc = np.insert(self.data_y, 0, self.data_x, axis=1)
        return "[" + ",".join(
                ["[" + ",".join(["%f" % val for val in row]) + "]" for row in conc]
            ) + "]"

    def _deserialize_data(self, data):
        """
            Internal method, should normally not be used!
            If you want to load data from a file, use the generic.io.file_parsers
            classes in combination with the load_data_from_generator instead!
            'data' argument should be a json string, containing a list of lists
            of x and y values, i.e.:
            [[x1, x2, ..., xn], [y11, y21, ..., yn1], ..., [y1m, y2m, ..., ynm]]
            If there are n data points and m+1 columns.
        """
        data = data.replace("nan", "'nan'")
        data = data.replace("-inf", "'-inf'")
        data = data.replace("+inf", "'+inf'")
        data = data.replace("inf", "'inf'")
        data = json.JSONDecoder().decode(data)
        return data

    def _set_from_serial_data(self, sdata):
        """Internal method, do not use!"""
        data = []
        try:
            data = self._deserialize_data(sdata)
        except ValueError:
            logger.exception("Failed to deserialize xy-data string `%s`" % sdata)
        if data != []:
            data = np.array(data, dtype=float)
            try:
                x = data[:, 0]
                y = data[:, 1]
            except IndexError:
                logger.exception("Failed to load xy-data from serial string: %s" % sdata)
            else:
                XYData.set_data(self, x, y)


    def load_data_from_generator(self, generator, clear=True):
        if clear: self.clear()
        for x, y in generator:
            self.append(x, y)

    # ------------------------------------------------------------
    #      X-Y Data Management Methods & Functions
    # ------------------------------------------------------------
    def _y_from_user(self, y_value):
        return np.array(y_value, ndmin=2, dtype=float)

    def set_data(self, x, y):
        """
            Sets data using the supplied x, y1, ..., yn arrays.
        """
        tempx = np.asanyarray(x)
        tempy = np.asanyarray(y)
        if tempy.ndim == 1:
            tempy = tempy.reshape((tempy.size, 1))
        if tempx.shape[0] != tempy.shape[0]:
            raise ValueError, "Shape mismatch: x (shape = %s) and y (shape = %s) data need to have compatible shapes!" % (tempx.shape, tempy.shape)
        self._data_x = tempx
        self._data_y = tempy

    def set_value(self, i, j, value):
        if i < len(self):
            if j == 0:
                self.data_x[i] = value
            elif j >= 1:
                self.data_y[i, j - 1] = np.array(value, dtype=float)
            else:
                raise IndexError, "Column indices must be positive values (is '%d')!" % j
        else:
            raise IndexError, "Row index '%d' out of bound!" % i

    def append(self, x, y):
        """
            Appends data using the supplied x, y1, ..., yn arrays.
        """
        data_x = np.append(self.data_x, x)
        _y = self._y_from_user(y)
        if self.data_y.size == 0:
            data_y = _y
        else:
            data_y = np.append(self.data_y, _y, axis=0)
        self.set_data(data_x, data_y)

    def insert(self, pos, x, y):
        """
            Inserts data using the supplied x, y1, ..., yn arrays at the given
            position.
        """
        self.data_x = np.insert(self.data_x, pos, x)
        self.data_y = np.insert(self.data_y, pos, self._y_from_user(y), axis=0)

    def remove_from_indeces(self, *indeces):
        if indeces != []:
            indeces = np.sort(indeces)[::-1]
            for index in indeces:
                self.set_data(
                    np.delete(self.data_x, index, axis=0),
                    np.delete(self.data_y, index, axis=0)
                )

    def clear(self):
        """
            Clears all x and y values.
        """
        self.set_data(np.zeros((0,), dtype=float), np.zeros((0, 0), dtype=float))

    # ------------------------------------------------------------
    #      Convenience Methods & Functions
    # ------------------------------------------------------------
    def get_xy_data(self, column=1):
        """
            Returns a two-tuple containing 1D-numpy arrays with the x-data and
            the y-data for a given column. If the column keyword is not passed, 
            the first column is returned.
        """
        if len(self) > 0:
            return self.data_x, self.data_y[:, column - 1]
        else:
            return np.array([], dtype=float), np.array([], dtype=float)

    def get_y_at_x(self, x, column=0):
        """ 
            Get the (interpolated) value for the y-column 'column' for
            a given x value
        """
        if self._data_x.size:
            return np.interp(x, self._data_x, self._data_y[:, column])
        else:
            return 0

    def get_y_name(self, column):
        """
            Returns the name of the given column. If the y_names attribute is 
            not properly set (e.g. too small or empty), it will return an empty
            string. This method is 'safer' to use then directly accessing the
            y_names attribute (may result in an IndexError).
        """
        try:
            return self.y_names[column]
        except IndexError:
            return ""

    # ------------------------------------------------------------
    #      Iterable & Indexable implementation
    # ------------------------------------------------------------
    def __len__(self):
        return len(self.data_x)

    def __getitem__(self, index):
        return self.data_x[index], self.data_y[index].tolist()

    def __iter__(self):
        for i in xrange(len(self)):
            yield self[i]

    pass # end of class

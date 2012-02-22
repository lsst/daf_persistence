#!/usr/bin/env python

# 
# LSST Data Management System
# Copyright 2008, 2009, 2010 LSST Corporation.
# 
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the LSST License Statement and 
# the GNU General Public License along with this program.  If not, 
# see <http://www.lsstcorp.org/LegalNotices/>.
#

# -*- python -*-

"""This module defines the ButlerSubset class and the ButlerDataRefs contained
within it as well as an iterator over the subset."""

from __future__ import with_statement

class ButlerSubset(object):

    """ButlerSubset is a container for ButlerDataRefs.  It represents a
    collection of data ids that can be used to obtain datasets of the type
    used when creating the collection or a compatible dataset type.  It can be
    thought of as the result of a query for datasets matching a partial data
    id.
    
    The ButlerDataRefs are generated at a specified level of the data id
    hierarchy.  If that is not the level at which datasets are specified, the
    ButlerDataRef.subItems() method may be used to dive further into the
    ButlerDataRefs.

    ButlerSubsets should generally be created using Butler.subset().

    This mechanism replaces the creation of butlers using partial dataIds.

    Public methods:

    __init__(self, butler, datasetType, level, dataId)

    __len__(self)

    __iter__(self)

    """

    def __init__(self, butler, datasetType, level, dataId):
        """
        Create a ButlerSubset by querying a butler for data ids matching a
        given partial data id for a given dataset type at a given hierarchy
        level.

        @param butler (Butler)    butler that is being queried.
        @param datasetType (str)  the type of dataset to query.
        @param level (str)        the hierarchy level to descend to.
        @param dataId (dict)      the (partial or complete) data id.
        """

        self.butler = butler
        self.datasetType = datasetType
        self.level = level
        self.dataId = dataId
        self.cache = []

        fmt = list(self.butler.getKeys(datasetType, level).iterkeys())
        for tuple in butler.queryMetadata(self.datasetType,
                level, fmt, self.dataId):
            tempId = dict(self.dataId)
            for i in xrange(len(fmt)):
                tempId[fmt[i]] = tuple[i]
            self.cache.append(tempId)

    def __len__(self):
        """
        Number of ButlerDataRefs in the ButlerSubset.

        @returns (int)
        """

        return len(self.cache)

    def __iter__(self):
        """
        Iterator over the ButlerDataRefs in the ButlerSubset.

        @returns (ButlerIterator)
        """

        return ButlerSubsetIterator(self)

class ButlerSubsetIterator(object):
    """
    An iterator over the ButlerDataRefs in a ButlerSubset.
    """

    def __init__(self, butlerSubset):
        self.butlerSubset = butlerSubset
        self.iter = iter(butlerSubset.cache)

    def __iter__(self):
        return self

    def next(self):
        return ButlerDataRef(self.butlerSubset, self.iter.next())

class ButlerDataRef(object):
    """
    A ButlerDataRef is a reference to a potential dataset or group of datasets
    that is portable between compatible dataset types.  As such, it can be
    used to create or retrieve datasets.

    ButlerDataRefs are (conceptually) created as elements of a ButlerSubset by
    Butler.subset().  They are initially specific to the dataset type passed
    to that call, but they may be used with any other compatible dataset type.
    Dataset type compatibility must be determined externally (or by trial and
    error).

    ButlerDataRefs may be created at any level of a data identifier hierarchy.
    If the level is not one at which datasets exist, a ButlerSubset
    with lower-level ButlerDataRefs can be created using
    ButlerDataRef.subItems().

    Public methods:

    get(self, datasetType=None)

    put(self, obj, datasetType=None)

    subItems(self, level=None)
    """

    def __init__(self, butlerSubset, dataId):
        """
        For internal use only.  ButlerDataRefs should only be created by
        ButlerSubset and ButlerSubsetIterator.
        """

        self.butlerSubset = butlerSubset
        self.dataId = dataId

    def get(self, datasetType=None):
        """
        Retrieve a dataset of the given type (or the type used when creating
        the ButlerSubset, if None) as specified by the ButlerDataRef.

        @param datasetType (str)  dataset type to retrieve.
        @returns object corresponding to the given dataset type.
        """

        if datasetType is None:
            datasetType = self.butlerSubset.datasetType
        return self.butlerSubset.butler.get(datasetType, self.dataId)

    def put(self, obj, datasetType=None):
        """
        Persist a dataset of the given type (or the type used when creating
        the ButlerSubset, if None) as specified by the ButlerDataRef.

        @param obj                object to persist.
        @param datasetType (str)  dataset type to persist.
        """

        if datasetType is None:
            datasetType = self.butlerSubset.datasetType
        self.butlerSubset.butler.put(obj, datasetType, self.dataId)

    def subLevels(self):
        """
        Return a list of the lower levels of the hierarchy than this
        ButlerDataRef.

        @returns (iterable)  list of strings with level keys."""

        return set(
                self.butlerSubset.butler.getKeys(
                    self.butlerSubset.datasetType).keys()
            ) - set(
                self.butlerSubset.butler.getKeys(
                    self.butlerSubset.datasetType,
                    self.butlerSubset.level).keys()
            )

    def subItems(self, level=None):
        """
        Generate a ButlerSubset at a lower level of the hierarchy than this
        ButlerDataRef, using it as a partial data id.  If level is None, a
        default lower level for the original ButlerSubset level and dataset
        type is used.

        @param level (str)   the hierarchy level to descend to.
        @returns (ButlerSubset) resulting from the lower-level query.
        """

        if level is None:
            level = self.butlerSubset.butler.mapper.getDefaultSubLevel(
                    self.butlerSubset.level)
        return self.butlerSubset.butler.subset(self.butlerSubset.datasetType,
                level, self.dataId)
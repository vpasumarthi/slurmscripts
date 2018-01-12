#!/usr/bin/env python

import numpy as np

from PyCT.io import read_poscar, write_poscar


def extract_cluster(srcFilePath, dstFilePath, siteIndexList, bondLimits,
                    terminatingElementType, terminatingBondDistance,
                    oxidationList, bridgeSearchDepth, chargeNeutral, prec):
    [latticeMatrix, elementTypes, nElements, totalElements, coordinateType,
     fractionalCoords, fileFormat] = read_poscar(srcFilePath)
    numSites = len(siteIndexList)
    elementTypes_consolidated = []
    uniqueElementTypes = set(elementTypes)
    numUniqueElementTypes = len(uniqueElementTypes)
    nElements_consolidated = np.zeros(numUniqueElementTypes, int)
    nElements_cumulative = nElements.cumsum()
    uniqueElementTypeIndex = -1
    for elementTypeIndex, elementType in enumerate(elementTypes):
        if elementType not in elementTypes_consolidated:
            uniqueElementTypeIndex += 1
            elementTypes_consolidated.append(elementType)
        nElements_consolidated[uniqueElementTypeIndex] += nElements[
                                                            elementTypeIndex]

    # Generate Bonding Neighbor List
    # No PBC implemented here.
    cartesianCoords = np.dot(fractionalCoords, latticeMatrix)
    bondingNeighborListIndices = np.empty(totalElements, dtype=object)
    elementTypeList = []
    for center_site_index, center_coord in enumerate(cartesianCoords):
        elementTypeIndex = np.where(
                                nElements_cumulative > center_site_index)[0][0]
        centerElementType = elementTypes[elementTypeIndex]
        elementTypeList.append(centerElementType)
        neighbor_list_indices = []
        for neighbor_site_index, neighbor_coord in enumerate(cartesianCoords):
            elementTypeIndex = np.where(
                            nElements_cumulative > neighbor_site_index)[0][0]
            neighborElementType = elementTypes[elementTypeIndex]
            refKeys = [':'.join([centerElementType, neighborElementType]),
                       ':'.join([neighborElementType, centerElementType])]
            if refKeys[0] in bondLimits:
                bondLimit = bondLimits[refKeys[0]]
            elif refKeys[1] in bondLimits:
                bondLimit = bondLimits[refKeys[1]]
            else:
                bondLimit = 0
            if bondLimit != 0:
                displacement_vector = neighbor_coord - center_coord
                displacement = np.linalg.norm(displacement_vector)
                if (0 < displacement < bondLimit):
                    neighbor_list_indices.append(neighbor_site_index)
        bondingNeighborListIndices[
                        center_site_index] = np.asarray(neighbor_list_indices)

    # Generate Cluster
    cluster_element_indices = np.asarray(siteIndexList)

    bridgeFound = 0
    bridgeDepth = 0
    searchIndexLists = np.empty(numSites, dtype=object)
    searchIndexLists.fill(np.empty(0, int))
    for siteIndex in range(numSites):
        searchIndexLists[siteIndex] = np.append(
                        searchIndexLists[siteIndex], siteIndexList[siteIndex])
    while (not bridgeFound and bridgeDepth < bridgeSearchDepth):
        for siteIndex, searchIndexList in enumerate(searchIndexLists):
            for searchIndex in searchIndexList:
                searchIndexLists[siteIndex] = np.append(
                                    searchIndexLists[siteIndex],
                                    bondingNeighborListIndices[searchIndex])
            searchIndexLists[siteIndex] = np.unique(searchIndexLists[
                                                                    siteIndex])
        bridgeIndices = np.intersect1d(searchIndexLists[0],
                                       searchIndexLists[1])
        bridgeDepth += 1
        if len(bridgeIndices):
            bridgeFound = 1

    # Add neighbor indices up to bridging species
    for siteIndex in range(numSites):
        cluster_element_indices = np.append(cluster_element_indices,
                                            searchIndexLists[siteIndex])
    cluster_element_indices = np.unique(cluster_element_indices)

    # Add terminating O sites
    for element_index in cluster_element_indices:
        element_type = elementTypeList[element_index]
        if element_type != 'O':
            cluster_element_indices = np.append(
                                    cluster_element_indices,
                                    bondingNeighborListIndices[element_index])
    cluster_element_indices = np.unique(cluster_element_indices)

    # Generate input parameters to writePOSCAR
    nElements_cluster = [0] * numUniqueElementTypes
    coordinates_cluster = []
    for element_index in cluster_element_indices:
        elementType = elementTypeList[element_index]
        elementTypeIndex = elementTypes_consolidated.index(elementType)
        nElements_cluster[elementTypeIndex] += 1
        coordinates_cluster.append(fractionalCoords[element_index])
    nonZeroIndices = [index for index in range(numUniqueElementTypes)
                      if nElements_cluster[index] != 0]
    nElements_cluster = [nElements_cluster[index] for index in nonZeroIndices]
    elementTypes_cluster = [elementTypes_consolidated[index]
                            for index in nonZeroIndices]

    # Generate coordinates of terminating H sites
    hCoordinatesList = []
    hBondParentElementIndices = []
    for element_index in cluster_element_indices:
        element_type = elementTypeList[element_index]
        if element_type == 'O':
            elementCartCoordinates = cartesianCoords[element_index]
            bondedIndices = bondingNeighborListIndices[element_index]
            for bondedIndex in bondedIndices:
                if bondedIndex not in cluster_element_indices:
                    bondedElementCartCoordinates = cartesianCoords[bondedIndex]
                    dispVector = (bondedElementCartCoordinates
                                  - elementCartCoordinates)
                    displacement = np.linalg.norm(dispVector)
                    hCartCoordinates = (elementCartCoordinates
                                        + (dispVector / displacement
                                           * terminatingBondDistance))
                    hFractCoordinates = np.dot(hCartCoordinates,
                                               np.linalg.inv(latticeMatrix))
                    hCoordinatesList.append(hFractCoordinates)
                    hBondParentElementIndices.append(element_index)
    hBondParentElementIndices = np.asarray(hBondParentElementIndices)
    numHSites = len(hCoordinatesList)

    # Ensure cluster charge neutrality
    if chargeNeutral:
        cluster_charge = 0
        for element_index, elementType in enumerate(elementTypes_cluster):
            element_charge = oxidationList[elementType]
            n_elements = nElements_cluster[element_index]
            cluster_charge += element_charge * n_elements
        cluster_charge += oxidationList['H'] * numHSites
        if cluster_charge % 2 == 0:
            numPairs = int(cluster_charge / 2)
            center_of_sites = (fractionalCoords[siteIndexList[0]]
                               + fractionalCoords[siteIndexList[1]]) / 2
            hDirList = []
            hDisp = []
            for hCoordinates in hCoordinatesList:
                dirVector = hCoordinates - center_of_sites
                disp = np.linalg.norm(np.dot(dirVector, latticeMatrix))
                hDirList.append(dirVector)
                hDisp.append(disp)
            hDirList = np.asarray(hDirList)
            hDisp = np.asarray(hDisp)
            sortIndices = hDisp.argsort()
            sortedHDirList = np.round(hDirList[sortIndices], prec)
            sortedHBondParentElementIndices = hBondParentElementIndices[
                                                                sortIndices]
            discardIndices = []
            numPairsDiscarded = 0
            maxIndex = numHSites - 1
            while (numPairsDiscarded != numPairs and maxIndex >= 1):
                # Check if the targeted O site has more than one proton attached
                if sum(sortedHBondParentElementIndices
                       == sortedHBondParentElementIndices[maxIndex]) > 1:
                    if (np.array_equal(sortedHDirList[maxIndex],
                                       -sortedHDirList[maxIndex - 1])):
                        discardIndices.extend([sortIndices[maxIndex - 1],
                                               sortIndices[maxIndex]])
                        sortedHBondParentElementIndices = np.delete(
                                    sortedHBondParentElementIndices,
                                    np.array([maxIndex - 1, maxIndex]))
                        maxIndex -= 2
                        numPairsDiscarded += 1
                    else:
                        maxIndex -= 1
                else:
                    maxIndex -= 1
            
            cluster_charge -= 2 * numPairsDiscarded * oxidationList['H']
            print('Final cluster charge: %d' % cluster_charge)
            hCoordinatesList = [hCoordinatesList[index]
                                for index in range(numHSites)
                                if index not in discardIndices]
            numHSites -= len(discardIndices)
    
    # Add terminating H coordinates
    if numHSites:
        elementTypes_cluster.append(terminatingElementType)
        nElements_cluster.append(numHSites)
        coordinates_cluster.extend(hCoordinatesList)

    write_poscar(srcFilePath, dstFilePath, fileFormat, elementTypes_cluster,
                 nElements_cluster, coordinateType, coordinates_cluster)
    return None

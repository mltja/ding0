from geopy.distance import vincenty
from shapely.geometry import LineString
from shapely.ops import transform


def calc_geo_branches_in_buffer(node, radius, radius_inc, proj):
    """ Determines branches in nodes' associated graph that are at least partly within buffer of `radius` from `node`.
        If there are no nodes, the buffer is successively extended by `radius_inc` until nodes are found.

    Args:
        node: origin node (e.g. LVStationDingo object) with associated shapely object (attribute `geo_data`) in any CRS
              (e.g. WGS84)
        radius: buffer radius in m
        radius_inc: radius increment in m
        proj: pyproj projection object: nodes' CRS to equidistant CRS (e.g. WGS84 -> ETRS)

    Returns:
        list of branches (NetworkX branch objects)

    """
    # TODO: check if this is the right place for this function!

    branches = []

    while not branches:
        node_shp = transform(proj, node.geo_data)
        buffer_zone_shp = node_shp.buffer(radius)
        for branch in node.grid.region.mv_grid_district.mv_grid.graph_edges():
            nodes = branch['adj_nodes']
            branch_shp = transform(proj, LineString([nodes[0].geo_data, nodes[1].geo_data]))
            if buffer_zone_shp.intersects(branch_shp):
                branches.append(branch)
        radius += radius_inc

    #branches = [_[0] for _ in sorted(branches, key=lambda x: x[1])]

    return branches


def calc_geo_dist_vincenty(node_source, node_target):
    """ Calculates the geodesic distance between `node_source` and `node_target`.
    Args:
        node_source: source node (Dingo object), member of _graph
        node_target: target node (Dingo object), member of _graph

    Returns:
        Distance in m
    """

    # notice: vincenty takes (lat,lon)
    return vincenty((node_source.geo_data.y, node_source.geo_data.x),
                    (node_target.geo_data.y, node_target.geo_data.x)).m


def calc_geo_dist_matrix_vincenty(nodes_pos):
    """ Calculates the geodesic distance between all nodes in `nodes_pos`. For every two points/coord it uses geopy's
    vincenty function (formula devised by Thaddeus Vincenty, with an accurate ellipsoidal model of the earth). As
    default ellipsoidal model of the earth WGS-84 is used. For more options see
    https://geopy.readthedocs.org/en/1.10.0/index.html?highlight=vincenty#geopy.distance.vincenty

    Args:
        nodes_pos: dictionary of nodes with positions,
                   Format: {'node_1': (x_1, y_1),
                            ...,
                            'node_n': (x_n, y_n)
                           }

    Returns:
        dictionary with distances between all nodes,
        Format: {'node_1': {'node_1': dist_11, ..., 'node_n': dist_1n},
                 ...,
                 'node_n': {'node_1': dist_n1, ..., 'node_n': dist_nn
                }

    Notice:
        x=longitude, y=latitude
    """

    matrix = {}

    for i in nodes_pos:
        pos_origin = tuple(nodes_pos[i])

        matrix[i] = {}

        for j in nodes_pos:
            pos_dest = tuple(nodes_pos[j])
            # notice: vincenty takes (lat,lon), thus the (x,y)/(lon,lat) tuple is reversed
            distance = vincenty(tuple(reversed(pos_origin)), tuple(reversed(pos_dest))).km
            matrix[i][j] = distance

    return matrix

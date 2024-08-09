import gdsfactory as gf
import matplotlib.pyplot as plt
import numpy as np
from gdsfactory.generic_tech import LAYER
from gdsfactory.generic_tech import get_generic_pdk
from gdsfactory.cross_section import ComponentAlongPath
import warnings
ignore = True
if ignore:
    warnings.filterwarnings("ignore")


def xmon(xmon_length , xmon_width, xmon_spacing, drive_spacing, flux_spacing):
    unit_convert = 1000
    xmon = gf.Component()
    cross = gf.components.cross(xmon_length, xmon_width)
    cross_polygons = cross.get_polygons()[LAYER.WG]
    r1 = gf.kdb.Region(cross_polygons)
    r2 = r1.sized(xmon_spacing*unit_convert)
    r3 = r2 - r1
    xmon.add_polygon(r3, layer=(5,0))
    xmon.add_port(name = 'drive', 
                        center = [(xmon.dxmin - drive_spacing), (xmon.dymin + xmon.dymax)/2],
                        width = 11,
                        orientation = 0,
                        layer = (5,0)
                        )
    xmon.add_port(name = 'flux', 
                        center = [(xmon.dxmin + xmon.dxmax)/2-14, (xmon.dymin - flux_spacing)], # this needs to be changed later
                        width = 11,
                        orientation = 0,
                        layer = (5,0)
                        )
    xmon.add_port(name = 'drive2', 
                        center = [(xmon.dxmax + drive_spacing), (xmon.dymin+xmon.dymax)/2], # this needs to be changed later
                        width = 11,
                        orientation = 180,
                        layer = (5,0)
                        )


    return xmon

def resize(shape, size):
    unit_convert = 1000
    shape_polygons = shape.get_polygons()[LAYER.WG] 
    r1 = gf.kdb.Region(shape_polygons)
    r2 = r1.sized(size*unit_convert)
    r3 = r2 - r1
    return r3

def top_connector_mod(connector_length, connector_depth, metal_spacing,size):
    connector_depth = connector_depth - size - metal_spacing
    # setting 
    outer_length = connector_length + 2*size + 2*metal_spacing
    outer_width = connector_depth + size + metal_spacing
    inner_length = connector_length + 2*size
    inner_width = connector_depth + size
    # print(f'outer_width = {outer_width}')

    c = gf.Component()
    container = gf.Component()
    outer_rect = gf.components.rectangle(size = (outer_length, outer_width))
    inner_rect = gf.components.rectangle(size = (inner_length, inner_width))
    outer_ref = container << outer_rect
    inner_ref = container << inner_rect
    inner_ref.dmove([(outer_length - inner_length) /2, 0])
    C = gf.boolean(A = outer_ref, B = inner_ref, operation='not', layer = (1,0))
    r = resize(C, size)
    c.add_polygon(r, layer=(5,0))
    return c, outer_width

def get_center(ref):
    return np.array([(ref.dxmax + ref.dxmin)/2, (ref.dymax + ref.dymin)/2])

epsilon_r = 11.45
epsilon_eff = (epsilon_r + 1)/2

def calculate_resonator_length(epsilon_eff, frequency):
    c = 299792458
    return c/(4*frequency*np.sqrt(epsilon_eff))

def calculate_resonator_frequency(epsilon_eff, length):
    c = 299792458
    return c/(np.sqrt(epsilon_eff) * 4 * length)

def one_cycle(length, radius):
    P = gf.Path()
    P += gf.path.straight(length=length)
    P += gf.path.arc(radius=radius, angle = 180, npoints=1000)  # Circular arc
    P += gf.path.straight(length=length)  # Straight section
    P += gf.path.arc(radius=radius, angle = -180, npoints=1000)  # Circular arc
    return P.length() 

def create_resonator(length, radius, number_of_cycle):
    P = gf.Path()

    for i in range(int(number_of_cycle)):
        if i == 0:
            P += gf.path.straight(length=length)
            P += gf.path.arc(radius=radius, angle = 90, npoints=100)  # Circular arc
            P += gf.path.straight(length=100)
            P += gf.path.arc(radius=radius, angle=90, npoints=100)

        else:
            P += gf.path.straight(length=length)
            P += gf.path.arc(radius=radius, angle = 180, npoints=100)  # Circular arc
        P += gf.path.straight(length=length)  # Straight section
        P += gf.path.arc(radius=radius, angle = -180, npoints=100)  # Circular arc
    
    P += gf.path.straight(length=length//2-radius)
    P += gf.path.arc(radius=radius, angle = 90, npoints=100)
    P += gf.path.straight(length = 180)
    return P.dmirror((1,0))

def resonator(epsilon_eff, frequency = 6.7e9, length = 300, radius = 30, air_bridge_flag = True, top_connector_depth = 80, air_bridge_spacing = 400):
    resonator_length_theory = calculate_resonator_length(epsilon_eff, frequency)*1e6
    number_of_cycle = 5
    Path = create_resonator(length, radius, number_of_cycle)
    Path_length = Path.length() + top_connector_depth
    print(f'Path length: {Path_length} um')
    print('resonator_frequency: ', f'{np.round(calculate_resonator_frequency(epsilon_eff, Path_length*1e-6)/1e9,3)} GHz' )

    resonator_width = 10
    tunnel_width = 6
    air_bridge_offset = 6 
    air_bridge_length = resonator_width + tunnel_width*2 + air_bridge_offset
    s1 = gf.Section(width=tunnel_width, offset=resonator_width/2 + tunnel_width/2, layer=(5, 0))
    s2 = gf.Section(width=tunnel_width, offset=-(resonator_width/2 + tunnel_width/2), layer=(5, 0))
    via = ComponentAlongPath(
        component= air_bridge(air_bridge_length),spacing=air_bridge_spacing, padding=0, offset=0,
    )

    x = gf.CrossSection(sections=[s1, s2], components_along_path=[via])

    c = gf.path.extrude(Path, cross_section=x)
    return c 

def resonator_airbridge(epsilon_eff, frequency = 6.7e9, length = 300, radius = 30, air_bridge_flag = True, top_connector_depth = 80, air_bridge_spacing = 400):
    resonator_length_theory = calculate_resonator_length(epsilon_eff, frequency)*1e6
    number_of_cycle = 5
    Path = create_resonator(length, radius, number_of_cycle)
    Path_length = Path.length() + top_connector_depth

    resonator_width = 10
    tunnel_width = 6
    air_bridge_offset = 6 
    air_bridge_length = resonator_width + tunnel_width*2 + air_bridge_offset
    s0 = gf.Section(width=resonator_width, offset=0, layer=(99,0))
    s1 = gf.Section(width=tunnel_width, offset=resonator_width/2 + tunnel_width/2, layer=(5, 0))
    s2 = gf.Section(width=tunnel_width, offset=-(resonator_width/2 + tunnel_width/2), layer=(5, 0))
    via = ComponentAlongPath(
        component= air_bridge(air_bridge_length),spacing=air_bridge_spacing, padding=0, offset=0,
    )

    x = gf.CrossSection(sections=[s1, s2], components_along_path=[via])

    # x = gf.CrossSection(sections=[s1, s2], )
    c = gf.path.extrude(Path, cross_section=x)
    return c 


@gf.cell
def air_bridge(xvr_length):

    if xvr_length >=5 and xvr_length <=16:
        xvr_width = 5
    elif xvr_length > 16 and xvr_length <= 27:
        xvr_width = 7.5
    elif xvr_length > 27 and xvr_length <= 32:
        xvr_width = 10
    else:
        raise Exception('xvr length is greater than 32')


    if xvr_length >=5 and xvr_length <=16:
        RR_length = 8
    elif xvr_length > 16 and xvr_length <= 27:
        RR_length = 10
    elif xvr_length > 27 and xvr_length <= 32:
        RR_length = 14 

    
    RR_width = xvr_width + 3
    Tether_width = RR_width + 2*1.5
    Tether_length = RR_length+2*1.5
    Tether_offset = (Tether_width - xvr_width)/2

    r3 = gf.kdb.DPolygon([(1.5, 1.5), (RR_length+1.5, 1.5), (RR_length+1.5, RR_width+1.5), (1.5, RR_width+1.5)])
    r4 = gf.kdb.DPolygon([(Tether_length+xvr_length+1.5, 1.5), (Tether_length+xvr_length+1.5+RR_length, 1.5), 
                          (Tether_length+xvr_length+1.5+RR_length, Tether_width-1.5), (Tether_length+xvr_length+1.5, Tether_width-1.5)])
    p_middle = gf.kdb.DPolygon([(Tether_length, Tether_offset), (Tether_length+xvr_length, Tether_offset), (Tether_length+xvr_length, Tether_width-Tether_offset), (Tether_length, Tether_width-Tether_offset)])
    p_left = r3.sized(1.5)
    p_right = r4.sized(1.5)


    left_canvas = gf.Component()
    right_canvas = gf.Component()
    mid_canvas = gf.Component()
    left_canvas.add_polygon(p_left, layer=(31, 0))
    right_canvas.add_polygon(p_right, layer=(31, 0))
    mid_canvas.add_polygon(p_middle, layer=(31, 0))

    c = gf.Component()
    left_ref = c << left_canvas
    right_ref = c << right_canvas
    mid_ref = c << mid_canvas

    c.add_polygon(r3, layer=(30, 0))
    c.add_polygon(r4, layer=(30, 0))
    c.flatten()

    rotated = gf.Component()
    qudit_ref = rotated << c
    qudit_ref.drotate(90)
    rotated.flatten()

    d = gf.Component()
    air_bridge_ref = d << rotated
    air_bridge_ref.dmovex(0-air_bridge_ref.dx)
    air_bridge_ref.dmovey(0-air_bridge_ref.dy)
    d.flatten()

    return d

@gf.cell
def qubit_resonator(xmon_spacing=20,
                    xmon_width = 40,
                    xmon_length = 420,

                    readout_connector_spacing = 4,
                    readout_connector_metal_spacing = 10,
                    readout_tunnel_width = 5,
                    top_connector_depth = 120,

                    drive_port_spacing = 4,
                    flux_port_spacing = 3,
                    ):

    # main canvas that holds everything
    canvas_qubit = gf.Component()

    # creating top connector. This will be added to temporary canvas
    # after creating resonator and deleting the middle piece, the gf.boolean Component will be added to main canvas
    # this serve to hold only the positional information relative to the xmon placement
    d = gf.Component() # temporary canvas for storing intermediate Component
    top_connector, top_connector_depth = top_connector_mod(connector_length=2*xmon_spacing+xmon_width+2*readout_connector_spacing, connector_depth=top_connector_depth, metal_spacing=readout_connector_metal_spacing, size = readout_tunnel_width)
    top_ref = d << top_connector

    # creating xmon
    drive_spacing = drive_port_spacing
    flux_spacing = flux_port_spacing 
    xmon_ref = canvas_qubit << xmon(xmon_length=xmon_length, xmon_width=xmon_width, xmon_spacing=xmon_spacing, drive_spacing=drive_spacing, flux_spacing=flux_spacing)

    # moving top connector to correct position
    dx = (xmon_ref.dxmax + xmon_ref.dxmin)/2 - (top_ref.dxmax + top_ref.dxmin)/2
    dy = xmon_ref.dymax  - top_ref.dymax
    top_ref.dmove([dx, dy + readout_tunnel_width * 2 + readout_connector_metal_spacing + readout_connector_spacing])

    my_resonator = resonator(epsilon_eff, top_connector_depth=top_connector_depth, air_bridge_spacing = 130)
    resonator_ref = canvas_qubit << my_resonator
    resonator_ref.dmove((get_center(top_ref) - get_center(resonator_ref)))
    resonator_ref.dmove([0, top_ref.dymax - resonator_ref.dymin-5])
    resonator_ymax = resonator_ref.dymax
    
    subtraction = gf.boolean(top_ref, resonator_ref, operation='and', layer=(5,0))
    merged = gf.boolean(top_ref, resonator_ref, operation='or', layer=(5,0))
    abc = gf.boolean(merged, subtraction, '-', layer=(5,0))
    abc_1 = gf.boolean(merged, abc, '-', layer=(5,0))
    temp = gf.Component()
    rec = gf.components.rectangle(size = (10, 5), centered=True, layer=(5,0))
    rec_ref = temp << rec
    rec_ref.dmove(
        ( - (rec_ref.dxmin + rec_ref.dxmax)/2 + (abc_1.dxmin + abc_1.dxmax)/2, 
                    - (rec_ref.dymin + rec_ref.dxmax)/2 + (abc_1.dymin + abc_1.dymax)/2 + 1.25)
                )
    remain = gf.boolean(top_ref, rec_ref, '-', layer=(5,0))
    remain_ref = canvas_qubit << remain

    canvas_qubit.flatten(merge=True)
    return canvas_qubit

qubit = qubit_resonator()
qubit.show()
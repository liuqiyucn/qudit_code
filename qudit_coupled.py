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

def resonator(epsilon_eff, frequency = 6.7e9, length = 300, radius = 30, air_bridge_flag = True, top_connector_depth = 80):
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
    s0 = gf.Section(width=resonator_width, offset=0, layer=(5,0))
    s1 = gf.Section(width=tunnel_width, offset=resonator_width/2 + tunnel_width/2, layer=(5, 0))
    s2 = gf.Section(width=tunnel_width, offset=-(resonator_width/2 + tunnel_width/2), layer=(5, 0))
    via = ComponentAlongPath(
        component= air_bridge(air_bridge_length),spacing=400, padding=250, offset=0,
    )

    if not air_bridge_flag:
        x = gf.CrossSection(sections=[s1, s2])
    else:
        x = gf.CrossSection(sections=[s1, s2], components_along_path=[via])

    c = gf.path.extrude(Path, cross_section=x)
    return c 

def JJ(FINGER_length, total_length):
    jj_width = 3
    assert (FINGER_length >= 0.1 and FINGER_length <= 6)
    length_left = (total_length - 2)/2
    length_right = length_left
    canvas_jj = gf.Component()
    left_rectangle_ref = canvas_jj << gf.components.rectangle(size=(length_left-1,jj_width), port_type='optical', layer=(20,0))
    taper = gf.components.taper2(
        length=0.5, 
        width1=jj_width, 
        width2=FINGER_length, 
        with_two_ports=True, 
        cross_section='strip', 
        port_names=('o1', 'o2'), 
        port_types=('optical', 'optical'), 
        with_bbox=True,
        layer = (20,0))
    taper_cover = gf.components.taper2(
        length=0.5, 
        width1=jj_width, 
        width2=FINGER_length, 
        with_two_ports=True, 
        cross_section='strip', 
        port_names=('o1', 'o2'), 
        port_types=('optical', 'optical'), 
        with_bbox=True,
        layer = (60,0))

    taper_ref = canvas_jj << taper
    taper_ref.connect("o1", left_rectangle_ref.ports['o3'], allow_layer_mismatch=True)
    finger_ref = canvas_jj << gf.components.rectangle(size=(1.36, FINGER_length), port_type='optical', layer = (20,0))
    finger_ref.connect("o1", taper_ref.ports['o2'], allow_layer_mismatch = True)

    taper_cover_ref = canvas_jj << taper_cover
    taper_cover_ref.connect("o1", left_rectangle_ref.ports['o3'], allow_layer_mismatch=True)
    finger_cover_ref = canvas_jj << gf.components.rectangle(size=(1.36+0.14, FINGER_length), port_type='optical', layer = (60,0))
    finger_cover_ref.connect("o1", taper_cover_ref.ports['o2'], allow_layer_mismatch = True)
    
    right_rectangle_ref = canvas_jj << gf.components.rectangle(size=(length_right-1,jj_width), port_type='optical', layer=(20,0))
    right_rectangle_ref.dmove(( finger_ref.dxmax + 0.14, 0 ))

    return canvas_jj


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
    # p_left = gf.kdb.DPolygon([(0,0), (Tether_width, 0), (Tether_width, Tether_width), (0, Tether_width)])
    # p_right = gf.kdb.DPolygon([(Tether_width+xvr_length, 0), (Tether_width*2+xvr_length, 0), (Tether_width*2+xvr_length, Tether_width), (Tether_width+xvr_length, Tether_width)])  
    # p_middle = gf.kdb.DPolygon([(Tether_width, Tether_offset), (Tether_width+xvr_length, Tether_offset), (Tether_width+xvr_length, Tether_width-Tether_offset), (Tether_width, Tether_width-Tether_offset)])
    # r1 = gf.kdb.Region(p_left.to_itype(gf.kcl.dbu))  # convert from um to DBU
    # r2 = gf.kdb.Region(p_right.to_itype(gf.kcl.dbu))  # convert from um to DBU
    # r3 = r1.sized(-1500)
    # r4 = r2.sized(-1500)

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

def qubit(
        xmon_length = 450,
        xmon_width = 48, 
        xmon_spacing = 20,
        readout_connector_spacing = 4,
        readout_tunnel_width = 5,
        readout_connector_metal_spacing = 15,
        drive_port_spacing = 4,
        flux_port_spacing = 3,
        overall_portWidth = 10,
        route_radius = 60,
        tranmission_width = 20,
        tranmission_tunnel_width = 12,
        tranmission_resonator_offset = 4,

        tranmission_width_drive = 10 ,
        tranmission_tunnel_width_drive = 6,
        tranmission_width_flux = 10 ,
        tranmission_tunnel_width_flux = 5,
        JJ_width = 0.230,
        JJ_width2 = 0.230,
        extrusion  = 4,

        coupled_spacing = 10,

        top_connector_depth = 90,
):
    unit_convert = 1e3

    qubit_spacing = coupled_spacing + xmon_length + 2*xmon_spacing

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

    my_resonator = resonator(epsilon_eff, top_connector_depth=top_connector_depth)
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





    # creating top connector. This will be added to temporary canvas
    # after creating resonator and deleting the middle piece, the gf.boolean Component will be added to main canvas
    # this serve to hold only the positional information relative to the xmon placement
    d = gf.Component() # temporary canvas for storing intermediate Component
    top_connector2, top_connector_depth = top_connector_mod(connector_length=2*xmon_spacing+xmon_width+2*readout_connector_spacing, connector_depth=top_connector_depth, metal_spacing=readout_connector_metal_spacing, size = readout_tunnel_width)
    top_ref2 = d << top_connector2

    # creating xmon
    drive_spacing = drive_port_spacing
    flux_spacing = flux_port_spacing 
    xmon_ref2 = canvas_qubit << xmon(xmon_length=xmon_length, xmon_width=xmon_width, xmon_spacing=xmon_spacing, drive_spacing=drive_spacing, flux_spacing=flux_spacing)

    # moving top connector to correct position
    dx = (xmon_ref2.dxmax + xmon_ref2.dxmin)/2 - (top_ref2.dxmax + top_ref2.dxmin)/2
    dy = xmon_ref2.dymax  - top_ref2.dymax
    top_ref2.dmove([dx, dy + readout_tunnel_width * 2 + readout_connector_metal_spacing + readout_connector_spacing])
    xmon_ref2.dmove((qubit_spacing, 0))
    top_ref2.dmove((qubit_spacing,0))

    my_resonator2 = resonator(epsilon_eff, top_connector_depth=top_connector_depth)
    resonator_ref2 = canvas_qubit << my_resonator2
    resonator_ref2.dmove((get_center(top_ref2) - get_center(resonator_ref2)))
    resonator_ref2.dmove([0, top_ref2.dymax - resonator_ref2.dymin-5])
    resonator_ymax = resonator_ref2.dymax

    
    subtraction2 = gf.boolean(top_ref2, resonator_ref2, operation='and', layer=(5,0))
    merged2 = gf.boolean(top_ref2, resonator_ref2, operation='or', layer=(5,0))
    abc2 = gf.boolean(merged2, subtraction2, '-', layer=(5,0))
    abc_1_2 = gf.boolean(merged2, abc2, '-', layer=(5,0))
    temp2 = gf.Component()
    rec2 = gf.components.rectangle(size = (10, 5), centered=True, layer=(5,0))
    rec_ref2 = temp2 << rec2
    rec_ref2.dmove(
        ( - (rec_ref2.dxmin + rec_ref2.dxmax)/2 + (abc_1_2.dxmin + abc_1_2.dxmax)/2, 
                    - (rec_ref2.dymin + rec_ref2.dxmax)/2 + (abc_1_2.dymin + abc_1_2.dymax)/2 + 1.25)
                )
    remain2 = gf.boolean(top_ref2, rec_ref2, '-', layer=(5,0))
    remain_ref2 = canvas_qubit << remain2



    ######################################
    # qubit and resonator finished
    ######################################

    # creating the boundary box to hold everything
    boundary = canvas_qubit << gf.components.rectangle(size=(5000, 5000), layer=(703, 0), centered=True, port_type='optical')
    port_width = overall_portWidth

    # creating the four ports for pad placement
    canvas_qubit.add_port(name='top', center=[(boundary.dxmax+boundary.dxmin)/2, boundary.dymax - 200], width = port_width,orientation=-90, layer = (5,0))
    canvas_qubit.add_port(name='right', center=[boundary.dxmax - 200, (boundary.dymax + boundary.dymin)/2], width = port_width,orientation=180, layer = (5,0))
    canvas_qubit.add_port(name='bot', center=[(boundary.dxmax+boundary.dxmin)/2, boundary.dymin + 200], width = port_width,orientation=90, layer = (5,0))
    canvas_qubit.add_port(name='left', center=[boundary.dxmin + 200, (boundary.dymax + boundary.dymin)/2], width = port_width,orientation=0, layer = (5,0))
    # pad = gf.read.import_gds(gdspath='pad.gds')

    # left
    pad = gf.read.import_gds(gdspath='pad2.gds')


    pad.add_port('back', center=[pad.dxmin,(pad.dymax + pad.dymin)/2], layer=(5,0), width=10, orientation=180)
    pad.add_port('front', center=[pad.dxmax,(pad.dymax + pad.dymin)/2], layer = (5,0), width=10, orientation=0)

    left_pad = canvas_qubit << pad
    left_pad.connect("back", canvas_qubit.ports['left'], allow_layer_mismatch=True)


    # tenporary drive for second qudit
    pad = gf.read.import_gds(gdspath='pad2.gds')


    pad.add_port('back', center=[pad.dxmin,(pad.dymax + pad.dymin)/2], layer=(5,0), width=10, orientation=180)
    pad.add_port('front', center=[pad.dxmax,(pad.dymax + pad.dymin)/2], layer = (5,0), width=10, orientation=0)

    left_pad2 = canvas_qubit << pad
    left_pad2.connect("back", canvas_qubit.ports['bot'], allow_layer_mismatch=True)






    # # bot
    # pad = gf.read.import_gds(gdspath='bot-connector2.gds')
    # pad.add_port('back', center=[pad.dxmin,(pad.dymax + pad.dymin)/2], layer=(5,0), width=10, orientation=180)
    # pad.add_port('front', center=[pad.dxmax,(pad.dymax + pad.dymin)/2], layer = (5,0), width=10, orientation=0)
    # bot_pad = canvas_qubit << pad
    # bot_pad.connect("back", canvas_qubit.ports['bot'], allow_layer_mismatch=True)

    pad = gf.read.import_gds(gdspath='pad_transmission2.gds')

    pad.add_port('back', center=[pad.dxmin,(pad.dymax + pad.dymin)/2], layer=(5,0), width=10, orientation=180)
    pad.add_port('front', center=[pad.dxmax,(pad.dymax + pad.dymin)/2], layer = (5,0), width=10, orientation=0)

    top_pad = canvas_qubit << pad
    top_pad.connect("back", canvas_qubit.ports['top'], allow_layer_mismatch=True)
    right_pad = canvas_qubit << pad
    right_pad.connect("back", canvas_qubit.ports['right'], allow_layer_mismatch=True)

    ######################################
    # pad added
    ######################################


    # transmission line
    inner = gf.Component()
    outer = gf.Component()
    xs_1 = gf.cross_section.cross_section(width=tranmission_width, layer=(5,0))
    xs_2 = gf.cross_section.cross_section(width=tranmission_width + 2*tranmission_tunnel_width, layer=(5,0))


    tranmission_turn = 800
    y_pos = resonator_ymax + tranmission_turn - 500
    y_pos2 = resonator_ymax + tranmission_width/2 + tranmission_tunnel_width + tranmission_resonator_offset

    route_inner = gf.routing.route_single_from_steps(
        inner, 
        port1 = top_pad.ports['front'],
        port2 = right_pad.ports['front'],
        allow_width_mismatch = False,
        cross_section = xs_1,
        steps = [
            {"x": 0, "y": y_pos},
            {"x": -1000, "y": y_pos},
            {"x": -1000, "y": y_pos2},
            {"x": y_pos2, "y": y_pos2},
            {"x": y_pos2, "y": 0},
        ],
        radius = route_radius,
    )

    route_outer = gf.routing.route_single_from_steps(
        outer, 
        port1 = top_pad.ports['front'],
        port2 = right_pad.ports['front'],
        allow_width_mismatch = False,
        cross_section = xs_2,
        steps = [
            {"x": 0, "y": y_pos},
            {"x": -1000, "y": y_pos},
            {"x": -1000, "y": y_pos2},
            {"x": y_pos2, "y": y_pos2},
            {"x": y_pos2, "y": 0},
        ],
        radius = route_radius,
    )

    tunnel = gf.boolean(A=outer, B = inner, operation='A-B', layer=(5,0))
    tunnel_ref = canvas_qubit << tunnel


    # bridge = gf.Component()
    # via = ComponentAlongPath(
    #     component= air_bridge(22),spacing=200, padding=2, offset=0,
    # )
    # xs_3_Section = gf.Section(width=tranmission_width + 2*tranmission_tunnel_width, layer=(5,0), port_names=('o1', 'o2'))
    # xs_3 = gf.CrossSection(sections=[xs_3_Section], components_along_path=[via])
    # route_bridge = gf.routing.route_single_from_steps(
    #     bridge, 
    #     port1 = top_pad.ports['front'],
    #     port2 = right_pad.ports['front'],
    #     allow_width_mismatch = False,
    #     cross_section = xs_3,
    #     steps = [
    #         {"x": 0, "y": y_pos},
    #         {"x": -500, "y": y_pos},
    #         {"x": -500, "y": y_pos2},
    #         {"x": y_pos2, "y": y_pos2},
    #         {"x": y_pos2, "y": 0},
    #     ],
    #     radius = route_radius,

    # )
    # extracted = bridge.extract(layers=((30, 0), (31,0),))
    # extracted.name = 'extracted'
    # canvas_qubit << extracted



    # Drive line
    drive_xmon = gf.read.import_gds(gdspath='drive-xmon.gds')
    drive_xmon.add_port('back', center=[drive_xmon.dxmin,(drive_xmon.dymax + drive_xmon.dymin)/2], layer=(5,0), width=10, orientation=180)
    drive_xmon.add_port('front', center=[drive_xmon.dxmax,(drive_xmon.dymax + drive_xmon.dymin)/2], layer = (5,0), width=10, orientation=180)
    drive_xmon_ref = canvas_qubit << drive_xmon
    drive_xmon_ref.connect("front", xmon_ref.ports['drive'], allow_layer_mismatch=True, allow_width_mismatch=True)

    inner = gf.Component()
    outer = gf.Component()
    bridge = gf.Component()
    xs_1 = gf.cross_section.cross_section(width=tranmission_width_drive, layer=(5,0))
    via = ComponentAlongPath(
        component= air_bridge(22),spacing=100, padding=2, offset=0,
    )
    xs_2 = gf.cross_section.cross_section(width=tranmission_width_drive + 2*tranmission_tunnel_width_drive, layer=(5,0))

    xs_3_Section = gf.Section(width=tranmission_tunnel_width_drive+2*tranmission_tunnel_width_drive, layer=(5,0), port_names=('o1', 'o2'))
    xs_3 = gf.CrossSection(sections=[xs_3_Section], components_along_path=[via])


    route_inner = gf.routing.route_single(
        inner, 
        port1 = left_pad.ports['front'],
        port2 = drive_xmon_ref.ports['back'],
        allow_width_mismatch = True,
        cross_section = xs_1,
        radius = route_radius,
    )

    route_outer = gf.routing.route_single(
        outer, 
        port1 = left_pad.ports['front'],
        port2 = drive_xmon_ref.ports['back'],
        allow_width_mismatch = True,
        cross_section = xs_2,
        radius = route_radius,
    )
    route_bridge = gf.routing.route_single(
        bridge, 
        port1 = left_pad.ports['front'],
        port2 = drive_xmon_ref.ports['back'],
        allow_width_mismatch = True,
        cross_section = xs_3,
        radius = route_radius,

    )



    drive_tunnel = gf.boolean(A=outer, B = inner, operation='A-B', layer=(5,0))
    drive_tunnel_ref = canvas_qubit << drive_tunnel

    extracted = bridge.extract(layers=((30, 0), (31,0),))
    extracted.name = 'extracted'
    canvas_qubit << extracted



    # 2nd Drive line
    drive_xmon = gf.read.import_gds(gdspath='drive-xmon.gds')
    drive_xmon.add_port('back', center=[drive_xmon.dxmin,(drive_xmon.dymax + drive_xmon.dymin)/2], layer=(5,0), width=10, orientation=180)
    drive_xmon.add_port('front', center=[drive_xmon.dxmax,(drive_xmon.dymax + drive_xmon.dymin)/2], layer = (5,0), width=10, orientation=180)
    drive_xmon_ref = canvas_qubit << drive_xmon
    drive_xmon_ref.connect("front", xmon_ref2.ports['drive2'], allow_layer_mismatch=True, allow_width_mismatch=True)


    inner = gf.Component()
    outer = gf.Component()
    bridge = gf.Component()
    xs_1 = gf.cross_section.cross_section(width=tranmission_width_drive, layer=(5,0))
    via = ComponentAlongPath(
        component= air_bridge(28),spacing=100, padding=2, offset=0,
    )
    xs_2 = gf.cross_section.cross_section(width=tranmission_width_drive + 2*tranmission_tunnel_width_drive, layer=(5,0))

    xs_3_Section = gf.Section(width=tranmission_tunnel_width_drive+2*tranmission_tunnel_width_drive, layer=(5,0), port_names=('o1', 'o2'))
    xs_3 = gf.CrossSection(sections=[xs_3_Section], components_along_path=[via])


    route_inner = gf.routing.route_single(
        inner, 
        port1 = left_pad2.ports['front'],
        port2 = drive_xmon_ref.ports['back'],
        allow_width_mismatch = True,
        cross_section = xs_1,
        radius = route_radius,
    )

    route_outer = gf.routing.route_single(
        outer, 
        port1 = left_pad2.ports['front'],
        port2 = drive_xmon_ref.ports['back'],
        allow_width_mismatch = True,
        cross_section = xs_2,
        radius = route_radius,
    )
    route_bridge = gf.routing.route_single(
        bridge, 
        port1 = left_pad2.ports['front'],
        port2 = drive_xmon_ref.ports['back'],
        allow_width_mismatch = True,
        cross_section = xs_3,
        radius = route_radius,

    )



    drive_tunnel = gf.boolean(A=outer, B = inner, operation='A-B', layer=(5,0))
    drive_tunnel_ref = canvas_qubit << drive_tunnel

    extracted = bridge.extract(layers=((30, 0), (31,0),))
    extracted.name = 'extracted'
    canvas_qubit << extracted





    # flux_xmon = gf.read.import_gds(gdspath='flux-xmon2.gds')
    # flux_xmon.layer

    # flux_xmon.add_port('top', center=[(-9.5+0.5)/2, flux_xmon.dymax+1], layer=(5,0), width=10, orientation=180)
    # flux_xmon.add_port('bot', center=[(-9.5+0.5)/2,flux_xmon.dymin], layer = (5,0), width=10, orientation=270)
    
    # flux_xmon_ref = canvas_qubit << flux_xmon
    # flux_xmon_ref.connect("top", xmon_ref.ports['flux'], allow_layer_mismatch=True, allow_width_mismatch=True)

    # inner = gf.Component()
    # outer = gf.Component()
    # xs_1 = gf.cross_section.cross_section(width=tranmission_width_flux, layer=(5,0))
    # xs_2 = gf.cross_section.cross_section(width=tranmission_width_flux + 2*tranmission_tunnel_width_flux, layer=(5,0))


    # route_inner = gf.routing.route_single(
    #     inner, 
    #     port1 = bot_pad.ports['front'],
    #     port2 = flux_xmon_ref.ports['bot'],
    #     allow_width_mismatch = True,
    #     cross_section = xs_1,
    #     radius = 60,
    # )

    # route_outer = gf.routing.route_single(
    #     outer, 
    #     port1 = bot_pad.ports['front'],
    #     port2 = flux_xmon_ref.ports['bot'],
    #     allow_width_mismatch = True,
    #     cross_section = xs_2,
    #     radius = 60,
    # )

    # flux_tunnel = gf.boolean(A=outer, B = inner, operation='A-B', layer=(5,0))
    # flux_tunnel_ref = canvas_qubit << flux_tunnel

    # bridge = gf.Component()
    # via = ComponentAlongPath(
    #     component= air_bridge(22),spacing=200, padding=2, offset=0,
    # )
    # via2 = ComponentAlongPath(
    #     component=gf.c.rectangle(size=(20, 20), centered=True, layer=(30,0)), spacing=200, padding=2
    # )
    # xs_3_Section = gf.Section(width=tranmission_tunnel_width_flux+2*tranmission_tunnel_width_flux, layer=(5,0), port_names=('o1', 'o2'))
    # xs_3 = gf.CrossSection(sections=[xs_3_Section], components_along_path=[via])
    # route_bridge = gf.routing.route_single(
    #     bridge, 
    #     port1 = bot_pad.ports['front'],
    #     port2 = flux_xmon_ref.ports['bot'],
    #     allow_width_mismatch = True,
    #     cross_section = xs_3,
    #     radius = 60,
    # )
    # extracted = bridge.extract(layers=((30, 0), (31,0),))
    # extracted.name = 'extracted'
    # canvas_qubit << extracted





    extrusion = extrusion
    jj = JJ(JJ_width, total_length=xmon_spacing)
    jj2 = JJ(JJ_width2, total_length=xmon_spacing)
    jj_ref1 = canvas_qubit << jj
    jj_ref2 = canvas_qubit << jj2
    jj_ref1.rotate(-90)
    jj_ref2.rotate(-90)
    jj_ref2.dmovex(20)
    
    jj_ref1.dmove(( 
        0 - jj_ref1.x-10,
        jj_ref1.dymax-xmon_length/2 - 1
    ))
    jj_ref2.dmove(( 
        0 - jj_ref2.x+10,
        jj_ref2.dymax-xmon_length/2 - 1
    ))
    
    top_rectangle = gf.components.rectangle(size=(jj_ref2.dxmax - jj_ref1.dxmin, 3), layer=(55, 0))
    bot_rectangle = gf.components.rectangle(size=(jj_ref2.dxmax - jj_ref1.dxmin, 3), layer=(55, 0))
    top_rectangle_ref = canvas_qubit << top_rectangle
    bot_rectangle_ref = canvas_qubit << bot_rectangle
    top_rectangle_ref_center = [(top_rectangle_ref.dxmax + top_rectangle_ref.dxmin)/2,(top_rectangle_ref.dymax + top_rectangle_ref.dymin)/2 ]
    bot_rectangle_ref_center = [(bot_rectangle_ref.dxmax + bot_rectangle_ref.dxmin)/2,(bot_rectangle_ref.dymax + bot_rectangle_ref.dymin)/2 ]
    top_rectangle_ref.dmove((
       (jj_ref1.dxmax + jj_ref2.dxmin)/2 - top_rectangle_ref_center[0] ,
       jj_ref1.dymax - top_rectangle_ref.dymin
    ))
    bot_rectangle_ref.dmove((
       (jj_ref1.dxmax + jj_ref2.dxmin)/2 - top_rectangle_ref_center[0] ,
       jj_ref1.dymin - bot_rectangle_ref.dymax
    ))


    # adding second JJ
    extrusion = extrusion
    jj = JJ(JJ_width, total_length=xmon_spacing)
    jj2 = JJ(JJ_width2, total_length=xmon_spacing)
    jj_ref1 = canvas_qubit << jj
    jj_ref2 = canvas_qubit << jj2
    jj_ref1.rotate(-90)
    jj_ref2.rotate(-90)
    jj_ref2.dmovex(20)
    
    jj_ref1.dmove(( 
        0 - jj_ref1.x-10+qubit_spacing,
        jj_ref1.dymax-xmon_length/2 - 1
    ))
    jj_ref2.dmove(( 
        0 - jj_ref2.x+10+qubit_spacing,
        jj_ref2.dymax-xmon_length/2 - 1
    )) 
   
    top_rectangle = gf.components.rectangle(size=(jj_ref2.dxmax - jj_ref1.dxmin, 3), layer=(55, 0))
    bot_rectangle = gf.components.rectangle(size=(jj_ref2.dxmax - jj_ref1.dxmin, 3), layer=(55, 0))
    top_rectangle_ref = canvas_qubit << top_rectangle
    bot_rectangle_ref = canvas_qubit << bot_rectangle
    top_rectangle_ref_center = [(top_rectangle_ref.dxmax + top_rectangle_ref.dxmin)/2,(top_rectangle_ref.dymax + top_rectangle_ref.dymin)/2 ]
    bot_rectangle_ref_center = [(bot_rectangle_ref.dxmax + bot_rectangle_ref.dxmin)/2,(bot_rectangle_ref.dymax + bot_rectangle_ref.dymin)/2 ]
    top_rectangle_ref.dmove((
       (jj_ref1.dxmax + jj_ref2.dxmin)/2 - top_rectangle_ref_center[0] ,
       jj_ref1.dymax - top_rectangle_ref.dymin
    ))
    bot_rectangle_ref.dmove((
       (jj_ref1.dxmax + jj_ref2.dxmin)/2 - top_rectangle_ref_center[0] ,
       jj_ref1.dymin - bot_rectangle_ref.dymax
    ))




    sss = canvas_qubit.extract(layers=((1,0)))
    remap = sss.remap_layers({(1, 0): (5, 0)})
    removed = canvas_qubit.remove_layers(layers=(1,0))
    canvas_qubit.add_ref(remap)

    rotated = gf.Component()
    qudit_ref = rotated << canvas_qubit
    qudit_ref.drotate(90)

    cut_off = gf.components.rectangle(size = (300, 100), layer=(5,0))
    cut_off_ref = rotated << cut_off
    cut_off_ref.dmove((
        -2500 - cut_off_ref.dxmin,
        2500 - cut_off_ref.dymax
    ))

    return rotated
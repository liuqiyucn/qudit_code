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


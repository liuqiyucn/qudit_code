from qudit import *
import pya
from kfactory.kcell import cell, save_layout_options
qubit = qubit(
        xmon_length = 420,
        xmon_width = 40, 
        xmon_spacing = 20,

        # readout connector section
        readout_connector_spacing = 4,
        readout_tunnel_width = 5,
        readout_connector_metal_spacing = 10,
        top_connector_depth=120,
        JJ_width=0.11,
        JJ_width2=0.20,

        #######################
        # parameters below shouldn't be changed
        #######################
        # drive port section
        drive_port_spacing = 4,
        flux_port_spacing = 3,

        # ports and routes specification
        overall_portWidth = 10,
        route_radius = 50,

        # tranmission line specification
        tranmission_width = 20,
        tranmission_tunnel_width = 12,
        tranmission_resonator_offset = 4,
)


# qubit = qubit(
#         xmon_length = 350,
#         xmon_width = 24, 
#         xmon_spacing = 20,

#         # readout connector section
#         readout_connector_spacing = 4,
#         readout_tunnel_width = 5,
#         readout_connector_metal_spacing = 10,
#         top_connector_depth=110,
#         JJ_width=0.11,
#         JJ_width2=0.20,

#         #######################
#         # parameters below shouldn't be changed
#         #######################
#         # drive port section
#         drive_port_spacing = 4,
#         flux_port_spacing = 3,

#         # ports and routes specification
#         overall_portWidth = 10,
#         route_radius = 50,

#         # tranmission line specification
#         tranmission_width = 20,
#         tranmission_tunnel_width = 12,
#         tranmission_resonator_offset = 4,
# )

# final = gf.Component()
# rectangle = gf.components.rectangle(size=(5000, 5000), layer=(5,0), centered=True)
# diff = gf.boolean(rectangle, qubit, 'A-B', layer1=(5,0), layer2=(5,0), layer=(5,0))
# diff.name = 'diff'
# final << diff

# extracted = qubit.extract(layers=((30,0), (31, 0), (60,0), (20, 0), (55,0), (703,0)))
# extracted.name = 'extracted'
# final << extracted 
# final.flatten(merge=True)
# final.show()
def write(qubit, is_DRC=True):
        options = save_layout_options()
        options.dbu = 0.0005
        if not is_DRC:
                qubit.flatten(merge=True)
                qubit.name = 'qudit'
                qubit.show()
                # qubit.write_gds('/Users/qiyu/Documents/gds-folder/QUDIT_tapeout1.gds', save_options=options)
        final = gf.Component()
        layer5 = qubit.extract( layers=((5,0),) )

        rectangle = gf.components.rectangle(size=(5000, 5000), layer=(5,0), centered=True)
        diff = gf.boolean(rectangle, layer5, 'A-B', layer1=(5,0), layer2=(5,0), layer=(100,0))
        diff.name = 'diff'
        removed = qubit.remove_layers(layers=((5,0),))
        extracted = diff.extract(layers=((100,0),))
        remap = extracted.remap_layers({(100, 0):(5,0)})

        final << qubit
        final << remap 
        final.flatten(merge=True)
        final.name = 'qudit'
        final.write_gds('/Users/qiyu/Documents/gds-folder/QUDIT_single2.gds', save_options=options)


write(qubit, is_DRC=False)

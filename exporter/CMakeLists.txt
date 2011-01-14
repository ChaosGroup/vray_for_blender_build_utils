set(INC 
	.
	..
    ../blenlib
    ../blenkernel
    ../blenloader
    ../makesdna
    ../makesrna
    ../windowmanager
    ../../../intern/guardedalloc
)

set(SRC
    exporter.c
    exporter_ops.c

    exporter.h
    exporter_ops.h
)

blender_add_lib(vb_mesh_exporter "${SRC}" "${INC}")

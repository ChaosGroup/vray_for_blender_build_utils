set(INC 
	.
    ../blenlib
    ../blenkernel
    ../blenloader
    ../makesdna
    ../makesrna
    ../windowmanager
    ../../../intern/guardedalloc
)

set(SRC
    exporter_ops.c

    exporter_ops.h
)

set(INC_SYS

)

blender_add_lib(vb_mesh_exporter "${SRC}" "${INC}" "${INC_SYS}")


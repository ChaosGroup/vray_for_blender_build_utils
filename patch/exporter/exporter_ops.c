/*

  V-Ray/Blender

  http://vray.cgdo.ru

  Author: Andrey M. Izrantsev (aka bdancer)
  E-Mail: izrantsev@cgdo.ru

  This program is free software; you can redistribute it and/or
  modify it under the terms of the GNU General Public License
  as published by the Free Software Foundation; either version 2
  of the License, or (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.

  All Rights Reserved. V-Ray(R) is a registered trademark of Chaos Software.

*/

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <pthread.h>
#include <time.h>

#include "BKE_main.h"
#include "BKE_scene.h"
#include "BKE_context.h"
#include "BKE_utildefines.h"
#include "BKE_library.h"
#include "BKE_DerivedMesh.h"
#include "BKE_fcurve.h"
#include "BKE_animsys.h"
#include "BKE_particle.h"
#include "BKE_global.h"
#include "BKE_report.h"
#include "BKE_object.h"
#include "BKE_mesh.h"
#include "BKE_curve.h"
#include "BKE_bvhutils.h"
#include "BKE_customdata.h"
#include "BKE_anim.h"
#include "BKE_depsgraph.h"
#include "BKE_displist.h"
#include "BKE_font.h"
#include "BKE_mball.h"

#include "DNA_scene_types.h"
#include "DNA_object_types.h"
#include "DNA_group_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meta_types.h"
#include "DNA_image_types.h"
#include "DNA_material_types.h"
#include "DNA_texture_types.h"
#include "DNA_camera_types.h"
#include "DNA_lamp_types.h"
#include "DNA_anim_types.h"
#include "DNA_action_types.h"
#include "DNA_curve_types.h"
#include "DNA_armature_types.h"
#include "DNA_modifier_types.h"
#include "DNA_windowmanager_types.h"
#include "DNA_particle_types.h"

#include "BLI_linklist.h"
#include "BLI_fileops.h"
#include "BLI_listbase.h"
#include "BLI_math.h"
#include "BLI_path_util.h"
#include "BLI_string.h"
#include "BLI_threads.h"

#include "PIL_time.h"

#include "RNA_access.h"
#include "RNA_define.h"

#ifdef WIN32
#ifdef htonl
#undef htonl
#undef htons
#undef ntohl
#undef ntohs
#define correctByteOrder(x) htonl(x)
#endif
#include <winsock.h>
#endif

#include "WM_api.h"
#include "WM_types.h"

#include "MEM_guardedalloc.h"

#include "exporter_ops.h"


#define USE_HAIR_DEBUG   0
#define BSPLINE_T(X)     ((X) * t_step)

#define TYPE_UV          5
#define MAX_MESH_THREADS 16

struct Material;
struct MTex;
struct Tex;

typedef struct UVLayer {
    char *name;
    int   id;
} UVLayer;

typedef struct ThreadData {
    Scene    *sce;
    Main     *bmain;
    LinkNode *objects;
    LinkNode *uvs;
    char     *filepath;
    int       id;
    int       animation;
    int       instances;
} ThreadData;


static pthread_mutex_t mtx= PTHREAD_MUTEX_INITIALIZER;

static ThreadData thread_data[MAX_MESH_THREADS];

static int debug= 0;


static int uvlayer_name_to_id(LinkNode *list, char *name)
{
    LinkNode *list_iter;
    UVLayer  *uv_layer;

    if(strcmp(name, "") == 0)
        return 1;

    list_iter= list;
    while(list_iter) {
        uv_layer= (UVLayer*)list_iter->link;
        if(strcmp(name, uv_layer->name) == 0)
            return uv_layer->id;
        list_iter= list_iter->next;
    }

    return 1;
}


static int uvlayer_in_list(LinkNode *list, char *name)
{
    LinkNode *list_iter;
    UVLayer  *uv_layer;

    list_iter= list;
    while(list_iter) {
        uv_layer= (UVLayer*)list_iter->link;
        if(strcmp(name, uv_layer->name) == 0)
            return 1;
        list_iter= list_iter->next;
    }
    return 0;
}


static int in_list(LinkNode *list, void *item)
{
    LinkNode *list_iter;

    if(!list)
        return 0;

    list_iter= list;
    while(list_iter) {
        if(list_iter->link == item)
            return 1;
        list_iter= list_iter->next;
    }
    return 0;
}


static void *uvlayer_ptr(char *name, int id)
{
    UVLayer *tmp;
    tmp= (UVLayer*)malloc(sizeof(UVLayer));
    tmp->name= name;
    tmp->id= id;
    return (void*)tmp;
}


static char *clean_string(char *str)
{
    char *tmp_str;
    int   i;

    tmp_str= (char*)malloc(MAX_IDPROP_NAME * sizeof(char));

    strncpy(tmp_str, str, MAX_IDPROP_NAME);

    for(i= 0; i < strlen(str); i++) {
        if(tmp_str[i]) {
            if(tmp_str[i] == '+')
                tmp_str[i]= 'p';
            else if(tmp_str[i] == '-')
                tmp_str[i]= 'm';
            else if(!((tmp_str[i] >= 'A' && tmp_str[i] <= 'Z') || (tmp_str[i] >= 'a' && tmp_str[i] <= 'z') || (tmp_str[i] >= '0' && tmp_str[i] <= '9')))
                tmp_str[i]= '_';
        }
    }

    return tmp_str;
}


static int write_edge_visibility(FILE *gfile,
                                 int k, unsigned long int *ev)
{
    if(k == 9) {
        fprintf(gfile, "%08X", htonl(*(int*)ev));
        *ev= 0;
        return 0;
    }
    return k + 1;
}


// B-Spline Interpolation
//
//  Algorithm: http://mathworld.wolfram.com/B-Spline.html
//
// TODO:
//  Simplify for degree = 2
//

static float
bspline_N (const int i, const int j, const float t, const float t_step)
{
    if(j == 0) {
        if((BSPLINE_T(i) < BSPLINE_T(i+1)) && (BSPLINE_T(i) <= t && t < BSPLINE_T(i+1)))
            return 1.0f;
        return 0.0f;
    }

    return bspline_N(i,j-1,t,t_step) * (t - BSPLINE_T(i)) / (BSPLINE_T(i+j) - BSPLINE_T(i)) + bspline_N(i+1,j-1,t,t_step) * ((BSPLINE_T(i+j+1) - t) / (BSPLINE_T(i+j+1) - BSPLINE_T(i+1)));
}

static float
bspline_C (const float P[], const int P_size, const int degree, const float t, const float t_step)
{
    int   i = 0;
    float S = 0.0f;

    for(i = 0; i <= P_size; ++i) {
        S += P[i] * bspline_N(i,degree,t,t_step);
    }

    return S;
}


// Write GeomMayaHair
//
static void
write_hair (FILE *gfile, Scene *sce, Main *bmain, Object *ob)
{
    int   c, i, p, s;
    float t;

    ParticleSystem   *psys;
    ParticleSettings *pset;

    ParticleSystemModifierData *psmd= NULL;

    ParticleData     *pa;

    HairKey          *hkey;

    ParticleCacheKey **child_cache;
    ParticleCacheKey  *child_key;
    int                child_total = 0;
    int                child_steps = 0;

    float     hairmat[4][4];
    float     segment[3];
    float     width= 0.001f;

    const int bspline_degree = 2;
    float     control_points[3][64]; // P
    float     knot_vector_step;
    int       segment_count;
    int       segment_interp_count;
    float     segment_step;

    PointerRNA rna_pset;
    PointerRNA VRayParticleSettings;
    PointerRNA VRayFur;

    char *cleared_string;

    int display_percentage;

    for(psys = ob->particlesystem.first; psys; psys = psys->next)
    {
        pset = psys->part;

        if(pset->type != PART_HAIR) {
            continue;
        }

        psmd = psys_get_modifier(ob, psys);

        if(!psmd) {
            continue;
        }

        RNA_id_pointer_create(&pset->id, &rna_pset);

        if(RNA_struct_find_property(&rna_pset, "vray")) {
            VRayParticleSettings= RNA_pointer_get(&rna_pset, "vray");

            if(RNA_struct_find_property(&VRayParticleSettings, "VRayFur")) {
                VRayFur= RNA_pointer_get(&VRayParticleSettings, "VRayFur");

                // Get hair width
                width= RNA_float_get(&VRayFur, "width");
            }
        }

        // B-spline interpolation
        segment_count        = (int)pow(2.0, pset->ren_step);
        segment_interp_count = segment_count + 2;

        // Store "Display percentage" setting
        display_percentage= pset->disp;
        pset->disp= 100;
        ob->recalc |= OB_RECALC_DATA;
        scene_update_tagged(bmain, sce);

        child_total = psys->totchildcache;
        child_cache = psys->childcache;

        cleared_string= clean_string(psys->name);
        fprintf(gfile, "GeomMayaHair HAIR%s", cleared_string);
        free(cleared_string);

        cleared_string= clean_string(pset->id.name+2);
        fprintf(gfile, "%s {", cleared_string);
        free(cleared_string);

        fprintf(gfile, "\n\tnum_hair_vertices= interpolate((%d,ListIntHex(\"", sce->r.cfra);
        for(p= 0, pa= psys->particles; p < psys->totpart; ++p, ++pa)
        {
            fprintf(gfile, "%08X", htonl(*(int*)&(segment_interp_count)));
        }
        for(p= 0; p < child_total; ++p)
        {
            child_key   = child_cache[p];
            child_steps = child_key->steps;

            fprintf(gfile, "%08X", htonl(*(int*)&(child_steps)));
        }
        fprintf(gfile,"\")));");

        fprintf(gfile, "\n\thair_vertices= interpolate((%d,ListVectorHex(\"", sce->r.cfra);
        for(p= 0, pa= psys->particles; p < psys->totpart; ++p, ++pa)
        {
            if(debug) {
                printf("\033[0;32mV-Ray/Blender:\033[0m Particle system: %s => Hair: %i\r", psys->name, p + 1);
                fflush(stdout);
            }
            
            psys_mat_hair_to_object(ob, psmd->dm, psmd->psys->part->from, pa, hairmat);

            // B-spline interpolation
            segment_step     = 1.0f / segment_count;
            knot_vector_step = 1.0f / pa->totkey;

            // Store control points
            for(s= 0, hkey= pa->hair; s < pa->totkey; ++s, ++hkey) {
                for(c= 0; c < 3; ++c) {
                    control_points[c][s] = hkey->co[c];
                }
#if USE_HAIR_DEBUG
                printf("Segment [%i] = %.3f,%.3f,%.3f\n", s, hkey->co[0], hkey->co[1], hkey->co[2]);
#endif
            }

            // Write interpolated points
            for(t= 0.0f; t <= 1.0; t += segment_step) {
                for(c= 0; c < 3; ++c) {
                    // Calculate interpolated coord
                    segment[c] = bspline_C(control_points[c], pa->totkey, bspline_degree, t, knot_vector_step);
                }
#if USE_HAIR_DEBUG
                printf("Interpolated [%.3f] = %.3f,%.3f,%.3f\n", t, segment[0], segment[1], segment[2]);
#endif
                mul_m4_v3(hairmat, segment);

                fprintf(gfile, "%08X%08X%08X",
                        htonl(*(int*)&(segment[0])),
                        htonl(*(int*)&(segment[1])),
                        htonl(*(int*)&(segment[2])));
            }

            // Implicit last point
            for(c= 0; c < 3; ++c) {
                segment[c] = control_points[c][pa->totkey-1];
            }
#if USE_HAIR_DEBUG
            printf("Implicit last point [%.3f] = %.3f,%.3f,%.3f\n", t, segment[0], segment[1], segment[2]);
#endif
            mul_m4_v3(hairmat, segment);

            fprintf(gfile, "%08X%08X%08X",
                    htonl(*(int*)&(segment[0])),
                    htonl(*(int*)&(segment[1])),
                    htonl(*(int*)&(segment[2])));
            
            // Without interpolation
            // for(s= 0, hkey= pa->hair; s < pa->totkey; ++s, ++hkey) {
            //     psys_mat_hair_to_object(ob, psmd->dm, psmd->psys->part->from, pa, hairmat);
            //     copy_v3_v3(segment, hkey->co);
            //     mul_m4_v3(hairmat, segment);
            //     fprintf(gfile, "%08X%08X%08X",
            //             htonl(*(int*)&(segment[0])),
            //             htonl(*(int*)&(segment[1])),
            //             htonl(*(int*)&(segment[2])));
            // }
        }
        if(debug) {
            printf("\n");
            fflush(stdout);
        }
        for(p= 0; p < child_total; ++p) {
            if(debug) {
                printf("\033[0;32mV-Ray/Blender:\033[0m Particle system: %s => Child hair: %i\r", psys->name, p+1);
                fflush(stdout);
            }

            child_key   = child_cache[p];
            child_steps = child_key->steps;
            for(s= 0; s < child_steps; s++, child_key++)
            {
                //psys_mat_hair_to_object(ob, psmd->dm, psmd->psys->part->from, pa, hairmat);
                fprintf(gfile, "%08X%08X%08X",
                        htonl(*(int*)&(child_key->co[0])),
                        htonl(*(int*)&(child_key->co[1])),
                        htonl(*(int*)&(child_key->co[2])));
            }
        }
        fprintf(gfile,"\")));");

        fprintf(gfile, "\n\twidths= interpolate((%d,ListFloatHex(\"", sce->r.cfra);
        for(p= 0, pa= psys->particles; p < psys->totpart; ++p, ++pa) {
            for(s= 0; s <= segment_interp_count; ++s) {
                fprintf(gfile, "%08X", htonl(*(int*)&(width)));
            }
        }
        for(p= 0; p < child_total; ++p) {
            child_key   = child_cache[p];
            child_steps = child_key->steps;
            
            for(s= 0; s < child_steps; ++s) {
                fprintf(gfile, "%08X", htonl(*(int*)&(width)));
            }
        }
        fprintf(gfile,"\")));\n");

        if(debug) {
            printf("\n");
        }

        fprintf(gfile,"}\n\n");

        // Restore "Display percentage" setting
        pset->disp= display_percentage;
        ob->recalc |= OB_RECALC_DATA;
        scene_update_tagged(bmain, sce);
    }
}


static void write_mesh(FILE *gfile,
                       Scene *sce, Object *ob, Mesh *mesh,
                       LinkNode *uv_list, int instances)
{
    Mesh   *me= ob->data;
    MFace  *face;
    MVert  *vert;

    CustomData *fdata;

    int    verts;
    int    fve[4];
    float *ve[4];
    float  no[3];

    int    matid= 0;
    int    hasUV= 0;
    int    maxLayer= 0;

    char  *lib_filename= (char*)malloc(FILE_MAX * sizeof(char));
    char  *cleared_string;

    PointerRNA   rna_me;
    PointerRNA   VRayMesh;
    PointerRNA   GeomStaticMesh;

    int          dynamic_geometry= 0;

    const int ft[6]= {0,1,2,2,3,0};

    unsigned long int ev= 0;

    int i, j, f, k, l;
    int u;

    if(debug)
        printf("Processing object \"%s\": mesh \"%s\"\n", ob->id.name, me->id.name);

    if(!mesh->totface)
        return;

    // Name format: ME<meshname>LI<libname>
    if(instances)
        cleared_string= clean_string(me->id.name+2);
    else
        cleared_string= clean_string(ob->id.name+2);

    fprintf(gfile,"GeomStaticMesh ME%s", cleared_string);
    free(cleared_string);

    if(me->id.lib) {
        BLI_split_file_part(me->id.lib->name+2, lib_filename, FILE_MAX);
        BLI_replace_extension(lib_filename, FILE_MAX, "");
        
        cleared_string= clean_string(lib_filename);
        fprintf(gfile,"LI%s", cleared_string);
        if(debug) {
            printf("V-Ray/Blender: Object: %s\n", ob->id.name+2);
            printf("  Mesh: %s\n", me->id.name+2);
            printf("    Lib filename: %s\n", lib_filename);
        }
        free(cleared_string);
        free(lib_filename);
    }
    fprintf(gfile," {\n");


    fprintf(gfile,"\tvertices= interpolate((%d, ListVectorHex(\"", sce->r.cfra);
    vert= mesh->mvert;
    for(f= 0; f < mesh->totvert; ++vert, ++f) {
        fprintf(gfile, "%08X%08X%08X",
                htonl(*(int*)&(vert->co[0])),
                htonl(*(int*)&(vert->co[1])),
                htonl(*(int*)&(vert->co[2])));
    }
    fprintf(gfile,"\")));\n");


    fprintf(gfile,"\tfaces= interpolate((%d, ListIntHex(\"", sce->r.cfra);
    face= mesh->mface;
    for(f= 0; f < mesh->totface; ++face, ++f) {
        if(face->v4)
            fprintf(gfile, "%08X%08X%08X%08X%08X%08X",
                    htonl(*(int*)&(face->v1)),
                    htonl(*(int*)&(face->v2)),
                    htonl(*(int*)&(face->v3)),
                    htonl(*(int*)&(face->v3)),
                    htonl(*(int*)&(face->v4)),
                    htonl(*(int*)&(face->v1)));
        else
            fprintf(gfile, "%08X%08X%08X",
                    htonl(*(int*)&(face->v1)),
                    htonl(*(int*)&(face->v2)),
                    htonl(*(int*)&(face->v3)));
    }
    fprintf(gfile,"\")));\n");


    fprintf(gfile,"\tnormals= interpolate((%d, ListVectorHex(\"", sce->r.cfra);
    face= mesh->mface;
    for(f= 0; f < mesh->totface; ++face, ++f) {
        fve[0]= face->v1;
        fve[1]= face->v2;
        fve[2]= face->v3;
        fve[3]= face->v4;

        // Get face normal
        for(i= 0; i < 3; i++)
            ve[i]= mesh->mvert[fve[i]].co;
        if(face->v4) {
            ve[3]= mesh->mvert[fve[3]].co;
            normal_quad_v3(no, ve[0], ve[1], ve[2], ve[3]);
        } else
            normal_tri_v3(no, ve[0], ve[1], ve[2]);

        if(face->v4) {
            for(i= 0; i < 6; i++) {
                // If face is smooth get vertex normal
                if(face->flag & ME_SMOOTH)
                    for(j= 0; j < 3; j++)
                        no[j]= (float)(mesh->mvert[fve[ft[i]]].no[j]/32767.0);

                fprintf(gfile, "%08X%08X%08X",
                        htonl(*(int*)&(no[0])),
                        htonl(*(int*)&(no[1])),
                        htonl(*(int*)&(no[2])));
            }
        } else {
            for(i= 0; i < 3; i++) {
                // If face is smooth get vertex normal
                if(face->flag & ME_SMOOTH)
                    for(j= 0; j < 3; j++)
                        no[j]= (float)(mesh->mvert[fve[i]].no[j]/32767.0);

                fprintf(gfile, "%08X%08X%08X",
                        htonl(*(int*)&(no[0])),
                        htonl(*(int*)&(no[1])),
                        htonl(*(int*)&(no[2])));
            }
        }
    }
    fprintf(gfile,"\")));\n");


    fprintf(gfile,"\tfaceNormals= interpolate((%d, ListIntHex(\"", sce->r.cfra);
    face= mesh->mface;
    k= 0;
    for(f= 0; f < mesh->totface; ++face, ++f) {
        if(mesh->mface[f].v4)
            verts= 6;
        else
            verts= 3;

        for(i= 0; i < verts; i++) {
            fprintf(gfile, "%08X", htonl(*(int*)&k));
            k++;
        }
    }
    fprintf(gfile,"\")));\n");


    fprintf(gfile,"\tface_mtlIDs= ListIntHex(\"");
    face= mesh->mface;
    for(f= 0; f < mesh->totface; ++face, ++f) {
        matid= face->mat_nr + 1;
        if(face->v4)
            fprintf(gfile, "%08X%08X", htonl(*(int*)&matid), htonl(*(int*)&matid));
        else
            fprintf(gfile, "%08X", htonl(*(int*)&matid));
    }
    fprintf(gfile,"\");\n");


    fprintf(gfile,"\tedge_visibility= ListIntHex(\"");
    ev= 0;
    if(mesh->totface <= 5) {
        face= mesh->mface;
        for(f= 0; f < mesh->totface; ++face, ++f) {
            if(face->v4) {
                ev= (ev << 6) | 27;
            } else {
                ev= (ev << 3) | 8;
            }
        }
        fprintf(gfile, "%08X", htonl(*(int*)&ev));
    } else {
        k= 0;
        face= mesh->mface;
        for(f= 0; f < mesh->totface; ++face, ++f) {
            if(face->v4) {
                ev= (ev << 3) | 3;
                k= write_edge_visibility(gfile, k, &ev);
                ev= (ev << 3) | 3;
                k= write_edge_visibility(gfile, k, &ev);
            } else {
                ev= (ev << 3) | 8;
                k= write_edge_visibility(gfile, k, &ev);
            }
        }

        if(k) {
            fprintf(gfile, "%08X", htonl(*(int*)&ev));
        }
    }
    fprintf(gfile,"\");\n");


    fdata= &mesh->fdata;

    hasUV= 0;
    maxLayer= 0;
    for(l= 1; l < fdata->totlayer; ++l) {
        if(fdata->layers[l].type == TYPE_UV) {
            hasUV= 1;
            maxLayer= l;
        }
    }

    if(hasUV) {
        fprintf(gfile,"\tmap_channels= interpolate((%d, List(", sce->r.cfra);
        for(l= 1; l < fdata->totlayer; ++l) {
            if(fdata->layers[l].type == TYPE_UV) {
                CustomData_set_layer_active(fdata, TYPE_UV, l-1);
                mesh_update_customdata_pointers(mesh);

                fprintf(gfile,"\n\t\t// %s", fdata->layers[l].name);
                fprintf(gfile,"\n\t\tList(%i,ListVectorHex(\"", uvlayer_name_to_id(uv_list, fdata->layers[l].name));

                face= mesh->mface;
                for(f= 0; f < mesh->totface; ++face, ++f) {
                    if(face->v4)
                        verts= 4;
                    else
                        verts= 3;
                    for(i= 0; i < verts; i++) {
                        fprintf(gfile, "%08X%08X00000000",
                                htonl(*(int*)&(mesh->mtface[f].uv[i][0])),
                                htonl(*(int*)&(mesh->mtface[f].uv[i][1])));
                    }
                }
                fprintf(gfile,"\"),");

                fprintf(gfile,"ListIntHex(\"");
                u= 0;
                face= mesh->mface;
                for(f = 0; f < mesh->totface; ++face, ++f) {
                    if(face->v4) {
                        fprintf(gfile, "%08X", htonl(*(int*)&u));
                        k= u+1;
                        fprintf(gfile, "%08X", htonl(*(int*)&k));
                        k= u+2;
                        fprintf(gfile, "%08X", htonl(*(int*)&k));
                        fprintf(gfile, "%08X", htonl(*(int*)&k));
                        k= u+3;
                        fprintf(gfile, "%08X", htonl(*(int*)&k));
                        fprintf(gfile, "%08X", htonl(*(int*)&u));
                        u+= 4;
                    } else {
                        fprintf(gfile, "%08X", htonl(*(int*)&u));
                        k= u+1;
                        fprintf(gfile, "%08X", htonl(*(int*)&k));
                        k= u+2;
                        fprintf(gfile, "%08X", htonl(*(int*)&k));
                        u+= 3;
                    }
                }
                fprintf(gfile,"\"))");

                if(l != maxLayer)
                    fprintf(gfile,",");
            }
        }
        fprintf(gfile,")));\n");
    }

    RNA_id_pointer_create(&me->id, &rna_me);
    if(RNA_struct_find_property(&rna_me, "vray")) {
        VRayMesh= RNA_pointer_get(&rna_me, "vray");
        if(RNA_struct_find_property(&VRayMesh, "GeomStaticMesh")) {
            GeomStaticMesh= RNA_pointer_get(&VRayMesh, "GeomStaticMesh");
            if(RNA_struct_find_property(&GeomStaticMesh, "dynamic_geometry")) {
                dynamic_geometry= RNA_boolean_get(&GeomStaticMesh, "dynamic_geometry");
            }
        }
    }

    // When this flag is true V-Ray will use dynamic geometry for this mesh.
    // Instead of copying the mesh many times in the BSP tree, only the bounding
    // box will be present many times and ray intersections will occur
    // in a separate object space BSP tree.
    fprintf(gfile,"\tdynamic_geometry= %i;\n", dynamic_geometry);

    fprintf(gfile,"}\n\n");
}


static Mesh *get_render_mesh(Scene *sce, Main *bmain, Object *ob)
{
    Object         *tmpobj= NULL;
    Curve          *tmpcu=  NULL;
    Mesh           *mesh=   NULL;
    DerivedMesh    *dm;
    CustomDataMask  mask= CD_MASK_MESH;

    /* perform the mesh extraction based on type */
    switch (ob->type) {
    case OB_FONT:
    case OB_CURVE:
    case OB_SURF:
        /* copies object and modifiers (but not the data) */
        tmpobj= copy_object( ob );
        tmpcu= (Curve *)tmpobj->data;
        tmpcu->id.us--;

        /* copies the data */
        tmpobj->data= copy_curve((Curve *)ob->data);

        /* get updated display list, and convert to a mesh */
        makeDispListCurveTypes(sce, tmpobj, 0);
        nurbs_to_mesh(tmpobj);

        /* nurbs_to_mesh changes the type tp a mesh, check it worked */
        if(tmpobj->type != OB_MESH) {
            free_libblock_us(&bmain->object, tmpobj);
            return NULL;
        }

        mesh= tmpobj->data;
        free_libblock_us(&bmain->object, tmpobj);
        break;
    case OB_MBALL:
        /* metaballs don't have modifiers, so just convert to mesh */
        ob= find_basis_mball(sce, ob);
        mesh= add_mesh("Mesh");
        mball_to_mesh(&ob->disp, mesh);
        break;
    case OB_MESH:
        /* apply modifiers and create mesh */
        dm= mesh_create_derived_render(sce, ob, mask);
        mesh= add_mesh("Mesh");
        DM_to_mesh(dm, mesh);
        dm->release(dm);
        break;
    default:
        return NULL;
    }

    /* we don't assign it to anything */
    mesh->id.us--;

    return mesh;
}


static int mesh_animated(Object *ob)
{
    ModifierData *mod;

    switch(ob->type) {
    case OB_CURVE:
    case OB_SURF:
    case OB_FONT: {
        Curve *cu= (Curve*)ob->data;
        if(cu->adt)
            return 1;
    }
    break;
    case OB_MBALL: {
        MetaBall *mb= (MetaBall*)ob->data;
        if(mb->adt)
            return 1;
    }
    break;
    case OB_MESH: {
        Mesh *me= (Mesh*)ob->data;
        if(me->adt)
            return 1;
    }
    break;
    default:
        break;
    }

    mod= (ModifierData*)ob->modifiers.first;
    while(mod) {
        switch (mod->type) {
        case eModifierType_Armature:
        case eModifierType_Array:
        case eModifierType_Displace:
        case eModifierType_Softbody:
        case eModifierType_Explode:
        case eModifierType_MeshDeform:
        case eModifierType_SimpleDeform:
        case eModifierType_ShapeKey:
        case eModifierType_Screw:
        case eModifierType_Warp:
            return 1;
        default:
            mod= mod->next;
        }
    }

    return 0;
}


static void *export_meshes_thread(void *ptr)
{
    struct ThreadData *td;

    double    time = 0.0;
    char      time_str[32];

    FILE     *gfile= NULL;
    char      filepath[FILE_MAX];

    Scene    *sce;
    Main     *bmain;
    Base     *base;
    Object   *ob;
    Mesh     *mesh;

    LinkNode *tdl;

    int       use_hair= 1;

    PointerRNA rna_scene;
    PointerRNA VRayScene;
    PointerRNA VRayExporter;

    td= (struct ThreadData*)ptr;

    sce=   td->sce;
    bmain= td->bmain;
    base= (Base*)sce->base.first;

    // Get export parameters from RNA
    RNA_id_pointer_create(&sce->id, &rna_scene);
    if(RNA_struct_find_property(&rna_scene, "vray")) {
        VRayScene= RNA_pointer_get(&rna_scene, "vray");

        if(RNA_struct_find_property(&VRayScene, "exporter")) {
            VRayExporter= RNA_pointer_get(&VRayScene, "exporter");

            // Export hair
            use_hair= RNA_boolean_get(&VRayExporter, "use_hair");
        }
    }

    if(debug) {
        time= PIL_check_seconds_timer();
        printf("V-Ray/Blender: Mesh export thread [%d]\n", td->id + 1);
    }
    sprintf(filepath, "%s_%.2d.vrscene", td->filepath, td->id);
    if(td->animation) {
        gfile= fopen(filepath, "a");
    } else {
        gfile= fopen(filepath, "w");
        fprintf(gfile,"// V-Ray/Blender 2.5\n");
        fprintf(gfile,"// Geometry file\n\n");
    }

    if(BLI_linklist_length(td->objects)) {
        tdl= td->objects;
        while(tdl) {
            ob= tdl->link;

            // Export hair
            if(use_hair) {
                pthread_mutex_lock(&mtx);

                write_hair(gfile, sce, bmain, ob);

                pthread_mutex_unlock(&mtx);
            }

            // Export mesh
            pthread_mutex_lock(&mtx);

            mesh= get_render_mesh(sce, bmain, ob);

            pthread_mutex_unlock(&mtx);

            if(mesh) {
                write_mesh(gfile, sce, ob, mesh, td->uvs, td->instances);

                pthread_mutex_lock(&mtx);

                /* remove the temporary mesh */
                free_mesh(mesh);
                BLI_remlink(&bmain->mesh, mesh);
                MEM_freeN(mesh);

                pthread_mutex_unlock(&mtx);
            }

            tdl= tdl->next;
        }
    }

    fclose(gfile);

    if(debug) {
        BLI_timestr(PIL_check_seconds_timer() - time, time_str);
        printf("V-Ray/Blender: Mesh export thread [%d] done [%s]\n", td->id + 1, time_str);
    }

    return NULL;
}


static void append_object(Scene *sce, LinkNode **objects, LinkNode **meshes, Object *ob,
                          int active_layers, int instances, int check_animated, int animation)
{
    GroupObject *gobject;
    Object      *gob;

    Mesh        *me;

    PointerRNA   rna_me;
    PointerRNA   VRayMesh;

    if(ob->dup_group) {
        gobject= (GroupObject*)ob->dup_group->gobject.first;
        while(gobject) {
            gob= gobject->ob;

            if(!in_list(*objects, (void*)gob)) {
                if(debug) {
                    printf("Group object: %s\n", gob->id.name);
                }
                append_object(sce, objects, meshes, gob,
                              active_layers, instances, check_animated, animation);
            }

            gobject= gobject->next;
        }
    }

    if(!ob->data)
        return;

    // TODO: geom_doHidden
    if(ob->restrictflag & OB_RESTRICT_RENDER)
        return;

    if(ob->type == OB_EMPTY   ||
       ob->type == OB_LAMP    ||
       ob->type == OB_CAMERA  ||
       ob->type == OB_LATTICE ||
       ob->type == OB_ARMATURE)
        return;

    if(active_layers)
        if(!(ob->lay & sce->lay))
            return;

    if(instances)
        if(in_list(*meshes, ob->data))
            return;

    if(ob->type == OB_MESH) {
        me= (Mesh*)ob->data;
        RNA_id_pointer_create(&me->id, &rna_me);
        if(RNA_struct_find_property(&rna_me, "vray")) {
            VRayMesh= RNA_pointer_get(&rna_me, "vray");
            if(RNA_struct_find_property(&VRayMesh, "override")) {
                if(RNA_boolean_get(&VRayMesh, "override"))
                    return;
            }
        }
    }

    if(animation)
        if(check_animated)
            if(!mesh_animated(ob))
                return;

    if(instances)
        BLI_linklist_prepend(meshes, ob->data);

    BLI_linklist_prepend(objects, ob);
}


static void export_meshes_threaded(char *filepath, Scene *sce, Main *bmain,
                                   int active_layers, int instances, int check_animated, int animation)
{
    Base     *base;
    Object   *ob;

    Material *ma;
    MTex     *mtex;
    Tex      *tex;

    pthread_t threads[MAX_MESH_THREADS];
    int       threads_count= 1;
    int       t;

    UVLayer  *uv_layer;
    LinkNode *uvs= NULL;
    int       uv_id= 0;

    LinkNode *list_iter= NULL;
    int       i;

    LinkNode *objects= NULL;
    LinkNode *objects_iter;
    LinkNode *meshes= NULL;

    PointerRNA rna_tex;
    PointerRNA VRayTexture;

    if(sce->r.mode & R_FIXED_THREADS)
        threads_count= sce->r.threads;
    else
        threads_count= BLI_system_thread_count();

    if(threads_count > MAX_MESH_THREADS)
        threads_count= MAX_MESH_THREADS;

    /*
      Preprocess textures to find proper UV channel indexes
    */
    for(ma= bmain->mat.first; ma; ma= ma->id.next) {
        if(debug) {
            printf("Material: %s\n", ma->id.name);
        }
        for(i= 0; i < MAX_MTEX; ++i) {
            if(ma->mtex) {
                mtex= ma->mtex[i];
                if(mtex) {
                    tex= mtex->tex;
                    if(tex) {
                        RNA_id_pointer_create(&tex->id, &rna_tex);
                        if(RNA_struct_find_property(&rna_tex, "vray")) {
                            VRayTexture= RNA_pointer_get(&rna_tex, "vray");
                            if(RNA_enum_get(&VRayTexture, "texture_coords")) { // 0 - object; 1 - UV
                                if(debug) {
                                    printf("Texture:    %s [UV layer: %s]\n", mtex->tex->id.name, mtex->uvname);
                                }
                                if(!(strcmp(mtex->uvname, "") == 0)) {
                                    if(!uvs) {
                                        BLI_linklist_prepend(&uvs, uvlayer_ptr(mtex->uvname, ++uv_id));
                                    } else {
                                        if(!(uvlayer_in_list(uvs, mtex->uvname))) {
                                            BLI_linklist_append(&uvs, uvlayer_ptr(mtex->uvname, ++uv_id));
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    if(debug) {
        list_iter= uvs;
        while(list_iter) {
            uv_layer= list_iter->link;
            if(uv_layer) {
                printf("UV.name= %s\n", uv_layer->name);
                printf("UV.id= %i\n", uv_layer->id);
            }
            list_iter= list_iter->next;
        }
    }

    /*
      Init thread data
    */
    for(t= 0; t < MAX_MESH_THREADS; ++t) {
        thread_data[t].sce= sce;
        thread_data[t].bmain= bmain;
        thread_data[t].id= t;
        thread_data[t].objects= NULL;
        thread_data[t].uvs= uvs;
        thread_data[t].filepath= filepath;
        thread_data[t].animation= animation;
        thread_data[t].instances= instances;
    }

    /*
      Collect objects
    */
    base= (Base*)sce->base.first;
    while(base) {
        ob= base->object;

        append_object(sce, &objects, &meshes, ob, active_layers, instances, check_animated, animation);

        base= base->next;
    }

    if(debug) {
        printf("Object list\n");
        objects_iter= objects;
        while(objects_iter) {
            ob= (Object*)objects_iter->link;

            printf("Object: %s\n", ob->id.name);

            objects_iter= objects_iter->next;
        }
    }

    /*
      Split object list to multiple lists
    */
    t= 0;
    objects_iter= objects;
    while(objects_iter) {
        ob= (Object*)objects_iter->link;

        BLI_linklist_prepend(&(thread_data[t].objects), ob);

        // TODO [LOW]: improve balancing using list sorting with ob->derivedFinal->numVertData
        if(t < threads_count - 1)
            t++;
        else
            t= 0;

        objects_iter= objects_iter->next;
    }

    if(debug) {
        for(t= 0; t < threads_count; ++t) {
            if(BLI_linklist_length(thread_data[t].objects)) {
                printf("Objects [%i]\n", t);
                list_iter= thread_data[t].objects;
                while(list_iter) {
                    ob= list_iter->link;
                    if(ob) {
                        printf("  %s\n", ob->id.name);
                    }
                    list_iter= list_iter->next;
                }
            }
        }
    }

    for(t= 0; t < threads_count; ++t) {
        pthread_create(&threads[t], NULL, export_meshes_thread, (void*) &thread_data[t]);
    }

    for(t= 0; t < threads_count; ++t) {
        pthread_join(threads[t], NULL);
    }

    for(t= 0; t < MAX_MESH_THREADS; ++t) {
        BLI_linklist_free(thread_data[t].objects, NULL);
    }

    BLI_linklist_free(uvs,     NULL);
    BLI_linklist_free(meshes,  NULL);
    BLI_linklist_free(objects, NULL);

    return;
}

static int export_scene(Scene *sce, Main *bmain, wmOperator *op)
{
    int     fra=   0;
    int     cfra=  0;

    char   *filepath= NULL;
    int     active_layers= 0;
    int     animation= 0;
    int     check_animated= 0;
    int     instances= 0;

    double  time;
    double  frame_time;
    char    time_str[32];

    if(!sce) {
        // Since render context is NULL
        // we need to get scene pointer from G
        // when operator is called from ops.render.render().
        // If operator is called separetely we use scene
        // from bContext.
        // TODO: get current scene not first
        sce= (Scene*)G.main->scene.first;
    }

    if(!sce)
        return OPERATOR_CANCELLED;

    if(RNA_property_is_set(op->ptr, "filepath")) {
        filepath= (char*)malloc(FILE_MAX * sizeof(char));
        RNA_string_get(op->ptr, "filepath", filepath);
    }

    if(RNA_property_is_set(op->ptr, "use_active_layers")) {
        active_layers= RNA_boolean_get(op->ptr, "use_active_layers");
    }

    if(RNA_property_is_set(op->ptr, "use_animation")) {
        animation= RNA_boolean_get(op->ptr, "use_animation");
    }

    if(RNA_property_is_set(op->ptr, "use_instances")) {
        instances= RNA_boolean_get(op->ptr, "use_instances");
    }

    if(RNA_property_is_set(op->ptr, "check_animated")) {
        check_animated= RNA_boolean_get(op->ptr, "check_animated");
    }

    if(RNA_property_is_set(op->ptr, "debug")) {
        debug= RNA_boolean_get(op->ptr, "debug");
    }

    time= PIL_check_seconds_timer();

    if(filepath) {
        printf("V-Ray/Blender: Exporting meshes...\n");

        if(animation) {
            cfra= sce->r.cfra;
            fra=  sce->r.sfra;

            printf("V-Ray/Blender: Exporting meshes for the first frame %-32i\n", fra);

            /* Export meshes for the start frame */
            sce->r.cfra= fra;
            CLAMP(sce->r.cfra, MINAFRAME, MAXFRAME);
            scene_update_for_newframe(bmain, sce, (1<<20) - 1);
            export_meshes_threaded(filepath, sce, bmain, active_layers, instances, 0, 0);
            fra+= sce->r.frame_step;

            /* Export meshes for the rest frames */
            while(fra <= sce->r.efra) {
                frame_time= PIL_check_seconds_timer();

                if(debug) {
                    printf("V-Ray/Blender: Exporting meshes for frame %-32i\n", fra);
                } else {
                    printf("V-Ray/Blender: Exporting meshes for frame %i...", fra);
                    fflush(stdout);
                }

                sce->r.cfra= fra;
                CLAMP(sce->r.cfra, MINAFRAME, MAXFRAME);
                scene_update_for_newframe(bmain, sce, (1<<20) - 1);
                export_meshes_threaded(filepath, sce, bmain, active_layers, instances, check_animated, 1);

                if(!debug) {
                    BLI_timestr(PIL_check_seconds_timer()-frame_time, time_str);
                    printf(" done [%s]\n", time_str);
                }

                fra+= sce->r.frame_step;
            }

            sce->r.cfra= cfra;
            CLAMP(sce->r.cfra, MINAFRAME, MAXFRAME);
            scene_update_for_newframe(bmain, sce, (1<<20) - 1);
        } else {
            export_meshes_threaded(filepath, sce, bmain, active_layers, instances, check_animated, 0);
        }

        BLI_timestr(PIL_check_seconds_timer()-time, time_str);
        printf("V-Ray/Blender: Exporting meshes done [%s]%-32s\n", time_str, " ");

        free(filepath);

        return OPERATOR_FINISHED;
    }

    return OPERATOR_CANCELLED;
}



/*
  OPERATOR
*/
static int export_scene_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
    /* Scene *scene= CTX_data_scene(C); */

    /* if(!scene) */
    /*     return OPERATOR_CANCELLED; */

    /* /\* only one render job at a time *\/ */
    /* if(WM_jobs_test(CTX_wm_manager(C), scene)) */
    /*  return OPERATOR_CANCELLED; */

    /* /\* stop all running jobs, currently previews frustrate Render *\/ */
    /* WM_jobs_stop_all(CTX_wm_manager(C)); */

    /* /\* handle UI stuff *\/ */
    /* WM_cursor_wait(1); */

    /* /\* add modal handler for ESC *\/ */
    /* WM_event_add_modal_handler(C, op); */

    return OPERATOR_RUNNING_MODAL;
}

static int export_scene_modal(bContext *C, wmOperator *op, wmEvent *event)
{
    switch(event->type) {
        case ESCKEY:
            /* cancel */
            return OPERATOR_CANCELLED;
        default:
            /* nothing to do */
            return OPERATOR_RUNNING_MODAL;
    }

    return OPERATOR_RUNNING_MODAL;
}

static int export_scene_exec(bContext *C, wmOperator *op)
{
    Main   *bmain= CTX_data_main(C);
    Scene  *sce=   CTX_data_scene(C);

    return export_scene(sce, bmain, op);
}

void VRAY_OT_export_meshes(wmOperatorType *ot)
{
    /* identifiers */
    ot->name=        "Export meshes";
    ot->idname=      "VRAY_OT_export_meshes";
    ot->description= "Export meshes in .vrscene format";

    /* api callbacks */
    ot->invoke= export_scene_invoke;
    ot->modal=  export_scene_modal;
    ot->exec=   export_scene_exec;

    RNA_def_string(ot->srna, "filepath", "", FILE_MAX, "Geometry filepath", "Geometry filepath");
    RNA_def_boolean(ot->srna, "use_active_layers", 0,  "Active layer",      "Export only active layers");
    RNA_def_boolean(ot->srna, "use_animation",     0,  "Animation",         "Export animation");
    RNA_def_boolean(ot->srna, "use_instances",     0,  "Instances",         "Use instances");
    RNA_def_boolean(ot->srna, "debug",             0,  "Debug",             "Debug mode");
    RNA_def_boolean(ot->srna, "check_animated",    0,  "Check animated",    "Try to detect if mesh is animated");
}

void ED_operatortypes_exporter(void)
{
    WM_operatortype_append(VRAY_OT_export_meshes);
}

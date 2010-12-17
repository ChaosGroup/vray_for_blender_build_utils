/*

 V-Ray/Blender

 http://vray.cgdo.ru

 Author: Andrey M. Izrantsev (aka bdancer)
 E-Mail: izrantsev@gmail.com

 This plugin is protected by the GNU General Public License v.2

 This program is free software: you can redioutibute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is dioutibuted in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.

 All Rights Reserved. V-Ray(R) is a registered trademark of Chaos Group

*/


#include "BKE_main.h"
#include "BKE_scene.h"
#include "BKE_context.h"

#include "DNA_windowmanager_types.h"

#include "WM_api.h"
#include "WM_types.h"

#include "RNA_define.h"

#include "exporter.h"
#include "exporter_ops.h"


void SCENE_OT_scene_export(wmOperatorType *ot)
{
    /* identifiers */
    ot->name= "Export scene";
    ot->idname= "SCENE_OT_scene_export";
    ot->description="Export meshes in .vrscene format.";

    /* api callbacks */
    ot->exec= export_scene;

    /* flags */
    ot->flag= 0;

    RNA_def_string(ot->srna, "filepath", "", FILE_MAX, "Geometry filepath", "Geometry filepath.");
    RNA_def_boolean(ot->srna, "use_active_layers", 0,  "Active layer",      "Export only active layers.");
    RNA_def_boolean(ot->srna, "use_animation",     0,  "Animation",         "Export animation.");
    //RNA_def_boolean_array(srna, "vb_render_layers", ARRAY_SIZE, NULL, "barr", "boolean array");
}


void ED_operatortypes_exporter(void)
{
	WM_operatortype_append(SCENE_OT_scene_export);
}


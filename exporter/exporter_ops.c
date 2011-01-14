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


#include "BKE_main.h"
#include "BKE_scene.h"
#include "BKE_context.h"

#include "DNA_windowmanager_types.h"

#include "WM_api.h"
#include "WM_types.h"

#include "RNA_define.h"

#include "exporter.h"
#include "exporter_ops.h"


void SCENE_OT_vray_export_meshes(wmOperatorType *ot)
{
    /* identifiers */
    ot->name= "Export meshes";
    ot->idname= "SCENE_OT_vray_export_meshes";
    ot->description="Export meshes in .vrscene format.";

    /* api callbacks */
	ot->poll= export_scene_poll;
    ot->exec= export_scene;

    /* flags */
    ot->flag= 0;

    RNA_def_string(ot->srna, "filepath", "", FILE_MAX, "Geometry filepath", "Geometry filepath.");
    RNA_def_boolean(ot->srna, "use_active_layers", 0,  "Active layer",      "Export only active layers.");
    RNA_def_boolean(ot->srna, "use_animation",     0,  "Animation",         "Export animation.");
    RNA_def_boolean(ot->srna, "use_instances",     0,  "Instances",         "Export instances.");
    RNA_def_boolean(ot->srna, "debug",             0,  "Debug",             "Debug mode.");
    RNA_def_boolean(ot->srna, "check_animated",    0,  "Check animated",    "Try to detect if mesh is animated.");
}


void ED_operatortypes_exporter(void)
{
	WM_operatortype_append(SCENE_OT_vray_export_meshes);
}


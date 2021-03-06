import bpy
from bpy.props import *
from bpy_extras.io_utils import ExportHelper

from ...functions import create_html_file


class EXPORT_OT_HTML(bpy.types.Operator, ExportHelper):
    """
    This appears in the tooltip of the operator and in the generated docs.
    """
    bl_idname = "export.html"  # this is important since its how bpy.ops.export.some_data is constructed
    bl_label = "Export to .html"

    # ExportHelper mixin class uses this
    filename_ext = ".html"

    filter_glob: StringProperty(
        default="*.html",
        options={'HIDDEN'},
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        return create_html_file(self.filepath)

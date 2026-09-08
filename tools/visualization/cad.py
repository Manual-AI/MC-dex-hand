"""Read named STEP occurrences in their assembled coordinates (millimetres)."""
from pathlib import Path

import numpy as np
import trimesh
from OCP.BRep import BRep_Tool
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.Bnd import Bnd_Box
from OCP.GeomAbs import GeomAbs_Cylinder
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label, TDF_LabelSequence
from OCP.TDocStd import TDocStd_Document
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS
from OCP.XCAFDoc import XCAFDoc_DocumentTool


def label_name(label):
    attr = TDataStd_Name()
    return attr.Get().ToExtString() if label.FindAttribute(TDataStd_Name.GetID_s(), attr) else "unnamed"


def occurrences(path):
    doc = TDocStd_Document(TCollection_ExtendedString("Manual-Dex"))
    reader = STEPCAFControl_Reader()
    reader.SetNameMode(True)
    reader.SetColorMode(False)
    if reader.ReadFile(str(path)) != IFSelect_RetDone or not reader.Transfer(doc):
        raise RuntimeError(f"Cannot read STEP assembly: {path}")
    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    roots = TDF_LabelSequence()
    tool.GetFreeShapes(roots)
    result = []

    def visit(label, location, parents):
        name = label_name(label)
        if tool.IsReference_s(label):
            reference = TDF_Label()
            tool.GetReferredShape_s(label, reference)
            location = location * tool.GetLocation_s(label)
            visit(reference, location, parents + [name])
        elif tool.IsAssembly_s(label):
            children = TDF_LabelSequence()
            tool.GetComponents_s(label, children)
            for i in range(1, children.Length() + 1):
                visit(children.Value(i), location, parents + [name])
        else:
            shape = tool.GetShape_s(label).Moved(location)
            bounds = Bnd_Box()
            BRepBndLib.Add_s(shape, bounds)
            result.append(dict(name=name, path="/".join(parents + [name]),
                               shape=shape, bounds=list(bounds.Get())))

    for i in range(1, roots.Length() + 1):
        visit(roots.Value(i), TopLoc_Location(), [])
    return result


def cylinders(shape):
    result = []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        surface = BRepAdaptor_Surface(TopoDS.Face_s(explorer.Current()))
        if surface.GetType() == GeomAbs_Cylinder:
            cylinder = surface.Cylinder()
            axis = cylinder.Axis()
            item = dict(radius=cylinder.Radius(), point=list(axis.Location().Coord()),
                        axis=list(axis.Direction().Coord()))
            if not any(np.allclose(item["point"], x["point"]) and
                       np.allclose(item["axis"], x["axis"]) and
                       abs(item["radius"] - x["radius"]) < 1e-5 for x in result):
                result.append(item)
        explorer.Next()
    return result


def mesh(shape, tolerance=0.20):
    """Tessellate B-rep faces; retain STEP placements and face winding."""
    BRepMesh_IncrementalMesh(shape, tolerance, False, 0.25, True).Perform()
    vertices, faces = [], []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        face = TopoDS.Face_s(explorer.Current())
        location = TopLoc_Location()
        triangles = BRep_Tool.Triangulation_s(face, location)
        if triangles is not None:
            offset = len(vertices)
            for i in range(1, triangles.NbNodes() + 1):
                vertices.append(triangles.Node(i).Transformed(location.Transformation()).Coord())
            for i in range(1, triangles.NbTriangles() + 1):
                indices = [offset + n - 1 for n in triangles.Triangle(i).Get()]
                faces.append(indices[::-1] if face.Orientation() == TopAbs_REVERSED else indices)
        explorer.Next()
    return trimesh.Trimesh(vertices=vertices, faces=faces, process=True)


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    items = occurrences(args.step)
    metadata = []
    for i, item in enumerate(items):
        surface = mesh(item["shape"])
        filename = f"{i:03d}_{item['name'].replace(' ', '_')}.stl"
        surface.export(args.out / filename)
        metadata.append(dict(index=i, name=item["name"], path=item["path"], file=filename,
                             bounds=surface.bounds.tolist(), center=surface.centroid.tolist(),
                             cylinders=cylinders(item["shape"])))
        if i % 10 == 0:
            print(f"Tessellated {i + 1}/{len(items)} occurrences", flush=True)
    (args.out / "cad.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Exported {len(items)} assembled occurrences to {args.out}", flush=True)

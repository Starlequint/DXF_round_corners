"""
author  Victor Lancieux
file    round_dxf.py
date    04/04/2025
brief   This script adds an arc fillet between three points in a DXF model.
usage   Laser cutting
"""
import ezdxf
import math

def distance(p0, p1):
    return math.sqrt((p1[0] - p0[0])**2 + (p1[1] - p0[1])**2)

def add_fillet(modelspace, p0, p1, p2, radius):
    """ Adds an arc fillet between three points 
    starting angle = angle between p0 and p1 ± π/2
    end angle = angle between p1 and p2 ± π/2
    center_x = p1_x + radius*cos(a_Σ)/sin(a_diff)
    center_y = p1_y + radius*sin(a_Σ)/sin(a_diff)
    """
    v1 = (p0[0] - p1[0], p0[1] - p1[1])
    v2 = (p2[0] - p1[0], p2[1] - p1[1])
    # atan2 return a value between π and -π
    angle1, angle2 = math.atan2(v1[1], v1[0]), math.atan2(v2[1], v2[0]) 
    a_diff = angle2 - angle1
    if a_diff < -math.pi:
        a_diff += 2*math.pi
    elif math.pi < a_diff:
        a_diff -= 2*math.pi
    
    if 0 < a_diff:
        start_a = angle1 - math.pi/2
        end_a = angle2 + math.pi/2
        start_angle, end_angle = math.degrees(end_a), math.degrees(start_a) #swap
    else:
        start_a = angle1 + math.pi/2
        end_a = angle2 - math.pi/2
        start_angle, end_angle = math.degrees(start_a), math.degrees(end_a)
    
    bisect_angle = (angle1 + angle2) / 2
    dist = radius / math.sin(abs(angle2 - angle1) / 2)
    fillet_center = (p1[0] + dist * math.cos(bisect_angle), 
                     p1[1] + dist * math.sin(bisect_angle))
    fillet_center2 = (p1[0] - dist * math.cos(bisect_angle), 
                     p1[1] - dist * math.sin(bisect_angle))
    mid_point = ((p0[0]+p2[0])/2, (p0[1]+p2[1])/2)
    if (distance(mid_point,fillet_center2) < distance(mid_point,fillet_center)):
        fillet_center = fillet_center2
    fillet_center = (round(fillet_center[0],3),round(fillet_center[1],3))
    
    modelspace.add_arc(fillet_center, radius, start_angle, end_angle)
    return ((round(fillet_center[0]+radius*math.cos(start_a),3),
             round(fillet_center[1]+radius*math.sin(start_a),3)),
            (round(fillet_center[0]+radius*math.cos(end_a),3), 
             round(fillet_center[1]+radius*math.sin(end_a),3)))

def checks(modelspace):
    """ Checks some restrictions for fusion360"""
    for e in modelspace:
        if e.dxftype() not in ["LINE", "ARC"]:
            print("Warrning : Unexpected entity:", e.dxftype())
    for e in modelspace:
        if hasattr(e.dxf, 'elevation'):
            e.dxf.elevation = 0
        if hasattr(e.dxf, 'start'):
            e.dxf.start = (e.dxf.start[0], e.dxf.start[1], 0)
        if hasattr(e.dxf, 'end'):
            e.dxf.end = (e.dxf.end[0], e.dxf.end[1], 0)
    for e in modelspace.query("POINT"):
        modelspace.delete_entity(e)
    print("Entities in DXF after filleting:")
    types = {}
    for e in modelspace:
        types[e.dxftype()] = types.get(e.dxftype(), 0) + 1
    print(types)

def main(dxf_file, output_file, radius, skip=True):
    doc = ezdxf.readfile(dxf_file)
    doc.header['$DWGCODEPAGE'] = 'ANSI_1252'
    modelspace = doc.modelspace()
    radius = abs(radius)
    nb_lines = 0
    for entity in modelspace.query("LWPOLYLINE OR POLYLINE"):
        points = entity.get_points()
        
        if 0 < len(points):
            first = (points[0][0], points[0][1])
            #print(first[0], first[1])
        memory = (points[-1][0], points[-1][1])
        for i in range(len(points)):
            p0, p1, p2 = points[i-1], points[i], points[(i+1)%len(points)]
            p0, p1, p2 = ((round(p0[0],3), round(p0[1],3)), 
                          (round(p1[0],3), round(p1[1],3)), 
                          (round(p2[0],3), round(p2[1],3)))
            
            if distance(p0, p1) > 2 * radius and distance(p1, p2) > 2 * radius:
                r = radius
            elif not(skip):
                r = min(distance(p0, p1), distance(p1, p2)) / 2
            else:
                r = 0
            if r != 0:
                new_p = add_fillet(modelspace, p0, p1, p2, r)
                if i != 0:
                    if distance(memory, new_p[0]) != 0:
                        modelspace.add_line(memory, new_p[0])
                        nb_lines += 1
                else:
                    first = (new_p[0][0], new_p[0][1])
                memory = (new_p[1][0], new_p[1][1])
            else:
                if i != 0:
                    modelspace.add_line(memory, p1)
                memory = (p1[0], p1[1])
        if 0 < len(points):
            modelspace.add_line(memory, first)
            nb_lines += 1
        modelspace.delete_entity(entity)
    checks(modelspace)
    doc.saveas(output_file, encoding='utf8')
    print(f"Rounded DXF saved as {output_file} with", nb_lines, "lines")

#main("victor.dxf", "victory.dxf", radius=5, skip=False)
main("square.dxf", "square_round_1.dxf", radius=5)
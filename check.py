# check.py
import numpy as np
import trimesh
import risk

def err(msg,report,d,file,filename,failed):
    report[d] += f"{filename},{msg}"
    failed.append(file)
    print(msg)
    return report,d,failed
def write(report,d,filename,has_hidden_void,voidnum=None,center_mass=None,bounds=None,void_shell=None,external_shells=None):
    report[d]+=f'{filename},' #id, file
    if has_hidden_void:
        report[d] += 'YES,' #has_hidden_void
        report[d] += f'{voidnum},' #voidnum
        report[d] += f'"{center_mass}",' #center_mass
        report[d] += f'"{bounds}",' # bounds
        report[d] += str(risk.calculate_void_risk(void_shell, external_shells))
    if not has_hidden_void:
        report[d] += 'NO,,,,'
    

def write_info(report,d,filename,num_shells,s,shell_amt_void,enclosures,has_hidden_void,voidnum=None,center_mass=None,bounds=None):
    report[d]+=f'{filename},' #id, file
    report[d] +=f'{num_shells},' # num_shells
    report[d]+=f'{s},' # shell_num
    report[d] += f'{shell_amt_void},'
    report[d] += f'{enclosures},'
    if has_hidden_void:
        report[d] += 'YES,' #has_hidden_void
        report[d] += f'{voidnum},' #voidnum
        report[d] += f'"{center_mass}",' #center_mass
        report[d] += f'"{bounds}"' # bounds
    if not has_hidden_void:
        report[d] += 'NO,,'


def check(args,filepath,filename,report,d,failed):
    # setup
    if args.directory:
        file=f'{filepath}/{filename}'
    if args.file:
        file = filename
    print("File:",file,end='...')
    mesh = trimesh.load_mesh(file)
    #mesh.remove_duplicate_faces()
    #mesh.remove_degenerate_faces()
    #b = trimesh.repair.broken_faces(mesh)
    #if any(b):
    #    print(b)
    #trimesh.repair.fill_holes(mesh)
    #trimesh.repair.fix_winding(mesh)
    # danger
    #trimesh.repair.fix_inversion(mesh)
    #trimesh.repair.fix_normals(mesh)

    r = mesh.split()
    num_shells = len(r)
    # immediate check to see if shells work out 
    if num_shells==0:
        msg = "Error: 0 shells in design. Please check or repair STL file."
        report,d,failed = err(msg,report,d,file,filename,failed)
        return report,d,failed
    
    ray_origin = []
    for s in range(num_shells):
        ray_origin.append([])
    ext = []
    v = [] 
    voidnum=1
    for s in range(num_shells):
        num_facets = len(r[s].triangles)
        if not r[s].is_watertight:
            msg = "Error: shell is not watertight. Please check or repair STL file."
            report,d,failed = err(msg,report,d,file,filename,failed)
            return report,d,failed
        shell_amt_void = ''
        enclosures = ''
        try:
            i_tri,i_ray,_ = r[s].ray.intersects_id(ray_origins=r[s].triangles_center,ray_directions=r[s].face_normals,multiple_hits=True,return_locations=True)
            i_dict = dict()
            for i in range(len(i_ray)):
                if i_ray[i] not in i_dict:
                    i_dict[i_ray[i].item()] = []
                if i_ray[i] == i_tri[i]:
                    continue
                    # don't add it; self-intersection
                i_dict[i_ray[i]].append(i_tri[i].item())
            #print(len(i_dict),len(r[s].triangles))

            # len(i_dict)==num_facets would be FALSE if...
            # ...there were some facets that didn't have ANY intersecting normals 
            # (even normals that only intersected with its own triangle)
            
            if len(i_dict)!=num_facets:
                #print(f'number of intersections:{len(i_dict)}. Number of facets: {num_facets}')
                msg = "Error: mismatch of facets and number of intersections. File may have been modified."
            #    report,d,failed = err(msg,report,d,file,filename,failed)
            #    return report,d,failed

            s_hidden_void=[False]*len(i_dict)
            for i in range(len(i_dict)):
                if i in i_dict.keys():
                    if i_dict[i]:
                        s_hidden_void[i] = True
            # logic:
            # if every ray has empty list (i.e. each ray only self-intersects): external
            # if some ray has some non-self intersection: some void 
            # if EVERY ray has a non-self intersection: hidden void 
            if all(s_hidden_void):
                shell_amt_void = '100'
                v.append(s)
            elif any(s_hidden_void):
                shell_amt_void = f'{(s_hidden_void.count(True)/num_facets)*100},' #shell_amt_void
                ext.append(s)
            elif not all(s_hidden_void):
                shell_amt_void = '0,'#shell_amt_void
                ext.append(s)
            
        except:
            msg = "runtime error"
            report,d,failed = err(msg,report,d,file,filename,failed)
            return report,d,failed
    if file not in failed:
        has_hidden_void = False
        # need to make sure each void shell is enclosed in some shell 
        if v and not ext:
            msg = "Error: Problem! there's a void shell(s) but no possible external shell"
            report,d,failed = err(msg,report,d,file,filename,failed)
            return report,d,failed
        if not ext and not v:
            msg = "Error: Not sure how you got here. empty design. :P"
            report,d,failed = err(msg,report,d,file,filename,failed)
            return report,d,failed
        if ext and not v:
            # ALL shells external
            if args.info:
                write_info(report,d,filename,num_shells,s,shell_amt_void,enclosures,has_hidden_void)
            else:
                write(report,d,filename,has_hidden_void)
            return report,d,failed
        while v:
            curr_void = v[0]
            # find which shell(s) it's inside - assuming we need just one 
            for e in ext:
                assert curr_void!=e,"Error: shell can't be void and external at the same time"
                pts = r[curr_void].vertices
                inside = r[e].contains(points=pts)
                if all(inside):
                    # congrats! it's an enclosed void 
                    enclosures=f"{curr_void} enclosed in {e}," #enclosures
                    has_hidden_void = True
                    if args.info:
                        write_info(report,d,filename,num_shells,s,shell_amt_void,enclosures,has_hidden_void,voidnum=voidnum,center_mass=np.around(r[curr_void].center_mass,3).tolist(),bounds=np.around(r[curr_void].bounds,3).tolist())
                    else:
                        write(report,d,filename,has_hidden_void,voidnum=voidnum,center_mass=np.around(r[curr_void].center_mass,3).tolist(),bounds=np.around(r[curr_void].bounds,3).tolist(),void_shell=r[curr_void],external_shells=[r[e]])
                    v.remove(curr_void)
                    if v:
                        # need to go through this file again...there are more voids to check enclosure for
                        voidnum+=1
                        report[d]+=f'\n'
                    break
            # what about the case where v is present but not enclosed in any shell?
            if not has_hidden_void: # after we've checked all the e's 
                msg = "Error: void shell is not enclosed"
                report,d,failed = err(msg,report,d,file,filename,failed)
                return report,d,failed
        return report,d,failed
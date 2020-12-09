import bpy

image_width = 1024
image_height = 1024

skip_bake = False



def add_image_node(nodes,image_width,image_height,name):
    node = nodes.new('ShaderNodeTexImage')
    image = bpy.data.images.new(name, width=image_width, height=image_height)
    node.image = image
    return node



def bake( bake_type, label, pass_filter={'NONE'} ):
    obj = bpy.context.active_object
    node_tree = obj.material_slots[0].material.node_tree
    nodes = node_tree.nodes
    links = node_tree.links
    for n in filter(lambda x:(x.type=='TEX_IMAGE') & (x.label==label) & (x.mute==False), nodes):
        new_n = nodes.new(type='ShaderNodeTexImage')
        try:
            new_n.image = n.image
            nodes.active = new_n
            print('baking:' + label);
            if skip_bake != True:
                bpy.ops.object.bake(type=bake_type, margin=16, use_selected_to_active=True, pass_filter = pass_filter )
            n.image.pack()
        finally:
            nodes.remove(new_n)
        break


def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


def get_bsdf(nodes):
    for n in nodes:
        if n.type=='GROUP':
            bsdf = get_bsdf(n.node_tree.nodes)
            if bsdf is not None:
                return bsdf
        else:
            if len(n.outputs)>0:
                if n.outputs[0].name=='BSDF':
                    return n



def add_new_bsdf_material():
    
    new_mat = bpy.data.materials.new(name="BakedBSDF")
    obj.data.materials.append(new_mat);
    new_mat.use_nodes = True
    nodes = new_mat.node_tree.nodes
    bsdf = nodes['Principled BSDF']
    links = new_mat.node_tree.links;

    diffuse = add_image_node(nodes, image_width, image_height, 'BakedDiffuse')
    diffuse.location = (-400,500)
    diffuse.label='diffuse'
    links.new(diffuse.outputs['Color'],bsdf.inputs['Base Color'])
    
    metallic = add_image_node(nodes, image_width, image_height, 'BakedMetallic')
    metallic.image.colorspace_settings.name = 'Non-Color'
    metallic.location = (-700,250)
    metallic.label='metallic'
    links.new(metallic.outputs['Color'],bsdf.inputs['Metallic'])
    
    roughness = add_image_node(nodes, image_width, image_height, 'BakedRoughness')
    roughness.image.colorspace_settings.name = 'Non-Color'
    roughness.location = (-400,100)
    roughness.label='roughness'
    links.new(roughness.outputs['Color'],bsdf.inputs['Roughness'])
    

    emission = add_image_node(nodes, image_width, image_height, 'BakedEmission')
    emission.location = (-700,-150)
    emission.label='emission'
    links.new(emission.outputs['Color'],bsdf.inputs['Emission'])
    

    normal = add_image_node(nodes, image_width, image_height, 'BakedNormal')
    normal.image.colorspace_settings.name = 'Non-Color'
    normal.location = (-700,-450)
    normal.label='normal'
    normal_map = nodes.new('ShaderNodeNormalMap')
    normal_map.location = (-250,-250)
    links.new(normal_map.outputs['Normal'],bsdf.inputs['Normal'])
    links.new(normal.outputs['Color'],normal_map.inputs['Color'])

    gltf_group_index = bpy.data.node_groups.find('glTF Settings')
    if gltf_group_index==-1:
        gltf_group = bpy.data.node_groups.new('glTF Settings', 'ShaderNodeTree')
        gltf_input = gltf_group.nodes.new('NodeGroupInput')
        gltf_input.location = (0,0)
        gltf_group.inputs.new('NodeSocketFloat','Occlusion')
    else:
        gltf_group = bpy.data.node_groups[gltf_group_index]
    gltf = nodes.new('ShaderNodeGroup')
    gltf.node_tree = gltf_group    
    gltf.location = (50,-400)
    
    ao = add_image_node(nodes, image_width, image_height, 'BakedAO')
    ao.image.colorspace_settings.name = 'Non-Color'
    ao.location = (-400,-500)
    ao.label='ao'
    links.new(ao.outputs['Color'],gltf.inputs['Occlusion'])




def Main():

    #---------------create material slot and material---------------

    obj = bpy.context.active_object
    if len(obj.material_slots)==0:
        add_new_bsdf_material();
        ShowMessageBox("Created Material. Please retry or change material BakedBSDF before retry.")
        return {'FINISHED'}


    #---------------bake ( metallic via emit ) and ( diffuse without metalic )---------------

    keep_slots = []
    keep_materials = []

    try:
        for o in bpy.context.selected_objects:
            if (o != bpy.context.active_object) & (o.type=='MESH'):
                for slot in o.material_slots:
                    
                    keep_slots.append(slot)
                    keep_materials.append(slot.material)
                    slot.material = slot.material.copy()
                    
                    bsdf = get_bsdf(slot.material.node_tree.nodes)
                    
                    #-------mettalic setting-------
                    
                    metallic = bsdf.inputs['Metallic'].default_value
                    bsdf.inputs['Emission'].default_value = [metallic,metallic,metallic,1]

                    #-------diffuse setting ( metallic off )-------
                    bsdf.inputs['Metallic'].default_value = 0
                    
        #ShowMessageBox("Baking Diffuse")
        #time.sleep(0)
        bake('DIFFUSE','diffuse',{'COLOR'})
        #ShowMessageBox("Baking Metallic")
        #time.sleep(0)
        bake('EMIT','metallic')

    finally:
        for i in range(len(keep_slots)):
            remove_material = keep_slots[i].material
            keep_slots[i].material = keep_materials[i]
            bpy.data.materials.remove(remove_material)




    #---------------bake basics---------------



    #ShowMessageBox("Baking Roughness")
    #time.sleep(0)
    bake('ROUGHNESS','roughness')
    #ShowMessageBox("Baking Ambient Occlusion")
    #time.sleep(0)
    bake('AO','ao')
    #ShowMessageBox("Baking Normal")
    #time.sleep(0)
    bake('NORMAL','normal')
    #ShowMessageBox("Baking Emission")
    #time.sleep(0)
    bake('EMIT','emission')

    ShowMessageBox("Baking Complete")
    print('bake:complete')

Main()

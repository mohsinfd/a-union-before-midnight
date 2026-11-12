"""Package six original unit illustrations for the R12 Japanese formations."""
from pathlib import Path
import hashlib
import json
import shutil

SOURCES = {
    'unique_akizuki':'exec-ab307d7c-b9c7-4e43-934f-4929c52ca831.png',
    'unique_torpedo':'exec-930afd4c-c8a1-43f4-86f1-56fbf580e9fe.png',
    'unique_patrol':'exec-d3178279-de78-4a70-9a6d-64f355eb1f57.png',
    'unique_patrol_early':'exec-d18271a0-edb0-4482-8069-7ada7a343ae9.png',
    'unique_teishin':'exec-abe2937b-3278-4774-b39d-6855e5b0d7ef.png',
    'unique_mixed':'exec-e262d3df-9ef8-4ccd-aa66-966b59a22518.png',
    'unique_kami':'exec-0b6de67c-4127-44cb-acbe-088db8308039.png',
}
PROMPTS = {
    'unique_akizuki': 'Use case: historical-scene. Create ONE original painted historical strategy-game unit illustration for a 1942 Japanese Akizuki-class anti-aircraft destroyer. Wide landscape composition, ship broadside in three-quarter view at sea, four distinctive twin 100-mm gun turrets, long sleek destroyer hull, restrained grey naval paint, faint smoke, distant carrier silhouettes only in background. Subject must be historically credible WWII Japanese destroyer, not a battleship or modern missile ship. Realistic military-history oil illustration, muted blue-grey sea and warm subdued highlights, fine detail and strong silhouette readable when reduced to 192x104 pixels. Keep entire primary ship safely within the middle horizontal band so a 400x116 banner crop remains useful. No text, lettering, captions, watermarks, UI, or decorative frame. This is new original artwork, not an archival photograph.',
    'unique_torpedo': 'Use case: historical-scene. ONE original military-history oil illustration for a WWII Japanese Type 93 oxygen-torpedo naval fitting. Wide landscape 3:1 composition. Main subject: a credible four-tube Japanese 610-mm deck torpedo launcher on the weathered steel deck of a 1930s-1940s destroyer, three-quarter close view showing long parallel launch tubes and their mechanical mount. Crew figures in period Japanese naval working clothing give scale; dusk blue sea in background, warm subdued deck lighting. No missiles, no modern electronics, no futuristic weapon, no aerial torpedo. Painterly realism matching a vintage grand-strategy unit card; bold clear machinery silhouette readable at 67x44. Keep launcher central with breathing room for banner crops. No labels, writing, watermark, interface, or frame. This should clearly differ from a whole-ship illustration.',
    'unique_patrol': 'Use case: historical-scene. ONE original WWII Japanese maritime patrol flying-boat unit illustration. Primary subject a historically credible Kawanishi H8K Type 2 flying boat: four propeller engines on a high broad straight wing, deep boat hull, single tall vertical tail, small underwing floats, green upper camouflage and pale underside with modest Japanese red roundels. Aircraft flies low in three-quarter side view above a blue-grey Pacific island lagoon, coral atoll and distant rain squall. Distinctive long-range patrol atmosphere, no dogfight. Wide 3:1 panoramic composition, the entire aircraft and all four engines visible, central with generous margins for small unit-card and event-banner crops. Muted detailed military-history oil painting, strong silhouette readable at 192x104, matches an elegant vintage grand-strategy game. No text, letters, watermark, interface, or decorative border. No jet, no modern plane, no carrier deck.',
    'unique_teishin': 'Use case: historical-scene. ONE original historical strategy-game illustration of Japanese Army Teishin airborne troops preparing for a 1942 parachute operation. Wide 3:1 landscape. Small group of credible WWII Japanese paratroopers in khaki uniforms, cloth-covered helmets, parachute harnesses and compact equipment at a tropical airstrip, a Japanese twin-engine Ki-57 style transport aircraft behind them, distant parachutes against humid morning sky. Central main figure and comrades readying harnesses, restrained purposeful scene, no exaggerated superhero poses, no modern tactical gear, no fantasy insignia. Realistic subdued military-history oil painting, warm earth and olive green tones, readable central silhouettes at 192x104, entire central group safely framed for a 400x116 crop. No text, captions, lettering, watermark, UI, or frame. Distinct from a generic infantry march illustration.',
    'unique_mixed': 'Use case: historical-scene. ONE original military-history painting for a Japanese Dokuritsu Konsei Ryodan independent mixed brigade, late 1930s China. Wide 3:1 landscape. Historically credible Japanese infantry in khaki field uniforms and steel helmets with a small wheeled field gun and pack animals at a railway station supply yard; central infantry officer and compact defensive gun position, railway and foothills receding behind. Depict an organised mixed infantry/artillery garrison formation, not a parade, not combat atrocities, not modern gear. Muted dusty ochre, olive and grey, realistic painterly vintage strategy-game unit art, strong silhouettes readable at 192x104. Keep main soldiers and field gun clustered in the central area for a 400x116 banner crop. No writing, captions, watermarks, UI, text, or decorative frame. Distinct visual subject from airborne troops.',
    'unique_kami': 'Use case: historical-scene. ONE original military-history unit illustration of a Japanese Type 2 Ka-Mi amphibious LIGHT TANK detachment, Pacific 1942-44. Wide 3:1 landscape. Main subject a small historically credible riveted Ka-Mi light tank, compact turret with short 37-mm gun, two-man turret proportions and attached boat-shaped buoyant front pontoon, crawling out of shallow surf onto a tropical beach. A second matching small amphibious tank farther behind, distant landing craft, subdued palm island horizon. Grey-green worn naval camouflage, wet metal and track details, modest scale, NOT a large modern tank, NOT a Sherman or landing tractor. Realistic muted grand-strategy oil painting, strong compact silhouette readable at 67x44 and192x104; keep main tank centred and fully visible with generous margins for event-banner crop. No text, caption, writing, watermark, interface or decorative frame.',
    'unique_patrol_early': 'Use case: historical-scene. ONE historically credible 1938 Japanese Kawanishi H6K Type 97 flying boat, NOT H8K. Original muted military-history oil painting for a grand-strategy game unit illustration. Long slender boat hull, very HIGH PARASOL wing mounted above fuselage on conspicuous struts, FOUR radial propeller engines in the parasol wing, open gap under wing, and DISTINCTIVE TWIN VERTICAL TAIL FINS on a wide horizontal tailplane. Wing floats. Three-quarter side view flying low over a Pacific lagoon, restrained green-grey period camouflage with red Japanese roundels. Aircraft entire silhouette clear and centred, broad margins, wide 3:1 panoramic landscape suitable for192x104 unit card and400x116 banner. This must visibly differ from the later H8K high-wing single-tail flying boat. No text, caption, writing, watermark, modern equipment, interface or border.',
}


# Additional reviewed originals are retained locally with their exact prompts.
for _row in json.loads((Path(__file__).parent/'R13_ART_SOURCES.json').read_text()):
    SOURCES[_row['key']]=Path(_row['source']).name
    PROMPTS[_row['key']]=_row['prompt']


def preserve_sources(art_root, workspace):
    art=Path(workspace)/'art';art.mkdir(exist_ok=True)
    rows=[]
    for key,name in SOURCES.items():
        source=Path(art_root)/name
        destination=art/(key+'.png')
        if not source.is_file():raise FileNotFoundError(source)
        shutil.copy2(source,destination)
        rows.append({'key':key,'source':str(source),'workspace':str(destination.resolve()),
                     'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
                     'mode':'built-in image_gen','prompt':PROMPTS[key]})
    (Path(workspace)/'UNIQUE_ART_MANIFEST.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    return rows


def install_cards(target, workspace, divisions, attachments):
    from PIL import Image, ImageOps
    target=Path(target);art=Path(workspace)/'art';rows=[]
    def save(im,path,size):
        # Preserve the complete ship/aircraft instead of cropping bow or wings.
        frame=Image.new('RGB',size,(25,31,32));subject=ImageOps.contain(im,size,Image.Resampling.LANCZOS)
        frame.paste(subject,((size[0]-subject.width)//2,(size[1]-subject.height)//2))
        frame.save(path)
    for kind,entries in [('division',divisions),('brigade',attachments)]:
        for unit,info in entries.items():
            key=info.get('artkey',info.get('art'))
            im=Image.open(art/(key+'.png')).convert('RGB')
            stages=len(info['years'])
            for model in range(stages):
                if unit=='d_14' and model==0:
                    im=Image.open(art/'unique_patrol_early.png').convert('RGB')
                elif unit=='d_14':
                    im=Image.open(art/'unique_patrol.png').convert('RGB')
                elif model in info.get('art_models',{}):
                    im=Image.open(art/(info['art_models'][model]+'.png')).convert('RGB')
                names = [(f'ill_div_JAP_{info["index"]}_{model}.bmp',(192,104)),
                         (f'JAP_model_{info["index"]}_{model}.bmp',(67,44))] if kind=='division' else [
                         (f'ill_bri_JAP_{info["index"]}_{model}.bmp',(192,104)),
                         (f'ill_bri_{info["index"]}_{model}.bmp',(192,104))]
                for name,size in names:
                    path=target/'gfx/interface/models'/name;save(im,path,size)
                    rows.append({'unit':unit,'model':model,'path':str(path),'size':size,
                                 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (Path(workspace)/'UNIQUE_ART_INSTALL.json').write_text(json.dumps(rows,indent=2)+'\n')
    return rows

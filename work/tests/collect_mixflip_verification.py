"""Collect only completed SHA-bound scoped evidence; never package, install or relabel reports."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work'))
import package_release as package
from run_mixflip_qa import validate as validate_stock


def main():
    digest=package.sha(ROOT/'outputs/FlipPets.apk');folder=ROOT/'work/qa-v03/device-files'
    expected={'qa.json':194,'composition-qa.json':68,'ui-switch-qa.json':15,'utility-qa.json':15,'pet-layout-qa.json':19,'mixflip-qa.json':80}
    reports=[]
    def collect(path,count,kind):
        data=json.loads(path.read_text(encoding='utf-8'))
        assert data['apkSha256']==digest and data['tested']==count and data['failed']==0 and not data.get('skipped')
        assert len(data['results'])==count and all(r['ok'] for r in data['results'])
        if path.name=='mixflip-qa.json':validate_stock(data,digest)
        reports.append(dict(kind=kind,path=path.relative_to(ROOT).as_posix(),sha256=package.sha(path),tested=count,failed=0))
    for name,count in expected.items():collect(folder/name,count,'APK')
    collect(folder/'mixflip-gallery-qa.json',9,'gallery')
    collect(ROOT/'work/qa-v03/runtime-v110.json',6,'virtual-cover')
    catalog=package.read(ROOT/'work/app/assets/catalog.json');package.validate_mixflip_import(catalog)
    paths={p for pet in catalog for p in pet['clips'].values()}
    checked=package.apk_checks(ROOT/'outputs/FlipPets.apk',catalog,paths)
    result=dict(schemaVersion=1,date='2026-10-11',apkSha256=digest,environment='Identity-verified emulator-5554, fliptest, Android16/API36 x86_64, host GPU/4GB; not HyperOS',apkChecks=sum(expected.values()),galleryChecks=9,virtualCoverChecks=6,binaryChecks=checked,reports=reports,catalogue=dict(entries=39,clipPaths=194,baseline33CanonicalSha256='cd49314203ab83a08263af0bf7fab17b714e267fdfbe526440cbf33d6f0a5b80',stockOriginalPag=18,stockOriginalForegrounds=12),sourceEvidence=dict(stockDecodeSamples=144,charlieSourceSamples=8,calibratedFullResolutionSamples=8,geometryCases=72,nativeFlowHostTests=35,provenanceGuardCases=5),notRerunForThisApk=['donor18-qa.json','mini-apps-qa.json','native-cards-qa.json'],physical=dict(phoneCommandsPerformed=False,phoneInstallPerformed=False,nativeUpdatePerformed=False,foldedCharlieFixed=False,exactRestoreProven=False,cameraClearanceProven=False),publication=dict(requiredApkChecks=479,releasePackaged=False,moduleRebuilt=False,commitPerformed=False,pushPerformed=False))
    target=ROOT/'work/research/mixflip-integration-verification.json';target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{sum(expected.values())} exact-APK checks, 9 gallery and 6 virtual-cover checks collected. No physical proof or release package.')


if __name__=='__main__':main()

import 'package:flutter_test/flutter_test.dart';
import 'package:fossil_menu/phi.dart';
void main(){
 test('phi match',(){expect(phiCheck(goldenRatio,1,1)['within_tolerance'],true);});
 test('nonmatch',(){expect(phiCheck(1,1,2)['within_tolerance'],false);});
 test('reject zero',(){expect(()=>phiCheck(0,1,2),throwsArgumentError);});
 test('symmetric',(){expect(phiCheck(1,2,2)['ratio'],phiCheck(2,1,2)['ratio']);});
}


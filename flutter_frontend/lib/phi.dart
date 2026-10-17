import 'dart:math' as math;
final double goldenRatio=(1+math.sqrt(5))/2;
Map<String,dynamic> phiCheck(double a,double b,double tolerance){
 if(!a.isFinite||!b.isFinite||a<=0||b<=0||!tolerance.isFinite||tolerance<0)throw ArgumentError('Positive finite lengths and nonnegative tolerance required');
 final ratio=math.max(a,b)/math.min(a,b);
 if(!ratio.isFinite)throw ArgumentError('Ratio overflow');
 final deviation=100*(ratio-goldenRatio).abs()/goldenRatio;
 return {'a':a,'b':b,'ratio':ratio,'phi':goldenRatio,'deviation_percent':deviation,'tolerance_percent':tolerance,'within_tolerance':deviation<=tolerance,'interpretation':'Numerical proximity only, not evidence of biological origin or a golden spiral'};
}

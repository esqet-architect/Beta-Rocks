import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'phi.dart';

// Steampunk Palette: Deep brass, oxidized copper, vacuum tube amber
const Color bgDark = Color(0xFF0C0906);
const Color panelBg = Color(0xFF1A120B);
const Color brassEdge = Color(0xFFC5A059);
const Color copperGlow = Color(0xFFE88A35);
const Color vacuumCyan = Color(0xFF4EE2DC);
const Color textGold = Color(0xFFD4AF37);

void main() {
  runApp(const ESQETApp());
}

class ESQETApp extends StatelessWidget {
  const ESQETApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: bgDark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: brassEdge,
          brightness: Brightness.dark,
          primary: brassEdge,
          surface: panelBg,
        ),
        inputDecorationTheme: const InputDecorationTheme(
          border: OutlineInputBorder(
            borderSide: BorderSide(color: brassEdge),
          ),
          enabledBorder: OutlineInputBorder(
            borderSide: BorderSide(color: brassEdge, width: 0.5),
          ),
          filled: true,
          fillColor: Color(0xFF120C06),
        ),
      ),
      home: const SteampunkFieldConsole(),
    );
  }
}

class SteampunkFieldConsole extends StatefulWidget {
  const SteampunkFieldConsole({super.key});

  @override
  State<SteampunkFieldConsole> createState() => _SteampunkFieldConsoleState();
}

class _SteampunkFieldConsoleState extends State<SteampunkFieldConsole>
    with SingleTickerProviderStateMixin {
  int page = 0;
  late AnimationController _radarController;

  // Survey State
  double radius = 300.0;
  bool isScanning = false;
  Map<String, dynamic>? currentAnomaly;
  String targetType = 'Fossil Matrix / Septarian Concretion';

  // Phi Lab Controllers
  final specimen = TextEditingController();
  final lengthA = TextEditingController();
  final lengthB = TextEditingController();
  final tolerance = TextEditingController(text: '2');
  final notes = TextEditingController();
  Map<String, dynamic>? phiResult;
  String? phiError;

  @override
  void initState() {
    super.initState();
    _radarController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 4),
    )..repeat();
  }

  @override
  void dispose() {
    _radarController.dispose();
    specimen.dispose();
    lengthA.dispose();
    lengthB.dispose();
    tolerance.dispose();
    notes.dispose();
    super.dispose();
  }

  void triggerAttractorScan() {
    setState(() {
      isScanning = true;
    });

    Timer(const Duration(milliseconds: 1500), () {
      final rng = math.Random();
      setState(() {
        isScanning = false;
        currentAnomaly = analyzeESQETField(
          lat: 38.2544 + (rng.nextDouble() - 0.5) * 0.02,
          lon: -104.6091 + (rng.nextDouble() - 0.5) * 0.02,
          magneticFieldUT: 45.0 + rng.nextDouble() * 15.0,
          radiusMeters: radius,
          drawIndex: rng.nextInt(9999),
        );
      });
    });
  }

  Widget steampunkPanel(String title, List<Widget> children) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: panelBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: brassEdge, width: 1.5),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withAlpha(180),
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.settings_ethernet, color: copperGlow, size: 18),
              const SizedBox(width: 8),
              Text(
                title,
                style: const TextStyle(
                  color: textGold,
                  fontSize: 14,
                  letterSpacing: 2.0,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ],
          ),
          const Divider(color: brassEdge, height: 20),
          ...children,
        ],
      ),
    );
  }

  Widget radarView() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        steampunkPanel(
          'ESQET FIELD COMPASS & ATTRACTOR',
          [
            const Text(
              'Deterministic Quantum-Seeded Exploration Unit\nE8 Lattice Bearing Projection Active.',
              style: TextStyle(color: vacuumCyan, fontSize: 12),
            ),
            const SizedBox(height: 16),
            Center(
              child: SizedBox(
                width: 260,
                height: 260,
                child: AnimatedBuilder(
                  animation: _radarController,
                  builder: (context, child) {
                    return CustomPaint(
                      painter: SteampunkRadarPainter(
                        animationValue: _radarController.value,
                        hasTarget: currentAnomaly != null,
                      ),
                    );
                  },
                ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                const Text('Scan Radius: ', style: TextStyle(color: textGold)),
                Expanded(
                  child: Slider(
                    value: radius,
                    min: 50,
                    max: 1000,
                    divisions: 19,
                    activeColor: copperGlow,
                    inactiveColor: Colors.brown,
                    label: '${radius.toInt()} m',
                    onChanged: (v) => setState(() => radius = v),
                  ),
                ),
                Text('${radius.toInt()} m', style: const TextStyle(color: copperGlow)),
              ],
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: targetType,
              dropdownColor: panelBg,
              decoration: const InputDecoration(labelText: 'Target Signature'),
              items: [
                'Fossil Matrix / Septarian Concretion',
                'Meteorite Iron-Nickel Vein',
                'Agate / Petrified Wood Pocket',
                'Quartzite Tectonic Fault Line',
              ].map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
              onChanged: (v) => setState(() => targetType = v!),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: copperGlow,
                  foregroundColor: bgDark,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                onPressed: isScanning ? null : triggerAttractorScan,
                icon: Icon(isScanning ? Icons.hourglass_top : Icons.radar),
                label: Text(
                  isScanning ? 'COMPUTING E8 TENSOR...' : 'CALCULATE FIELD ATTRACTOR',
                  style: const TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1.5),
                ),
              ),
            ),
          ],
        ),
        if (currentAnomaly != null)
          steampunkPanel('TARGET COORDINATE SOLUTION', [
            Text(
              'LAT: ${currentAnomaly!['latitude'].toStringAsFixed(6)}',
              style: const TextStyle(fontSize: 16, color: vacuumCyan),
            ),
            Text(
              'LON: ${currentAnomaly!['longitude'].toStringAsFixed(6)}',
              style: const TextStyle(fontSize: 16, color: vacuumCyan),
            ),
            const SizedBox(height: 10),
            Text('E8 Transect Bearing: ${currentAnomaly!['e8_transect_bearing_deg'].toStringAsFixed(1)}°'),
            Text('Vacuum Coherence (φ): ${currentAnomaly!['vacuum_coherence_phi'].toStringAsFixed(4)}'),
            Text('Poisson Significance Z: ${currentAnomaly!['poisson_significance_z'].toStringAsFixed(2)}'),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                border: Border.all(color: copperGlow),
                color: Colors.black45,
              ),
              child: Text(
                'STATUS: ${currentAnomaly!['target_classification']}',
                style: const TextStyle(color: copperGlow, fontWeight: FontWeight.bold),
              ),
            ),
          ]),
      ],
    );
  }

  Widget phiLabView() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        steampunkPanel('GOLDEN-RATIO COHERENCE LAB', [
          TextField(
            controller: specimen,
            decoration: const InputDecoration(labelText: 'Specimen Designation'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: lengthA,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(labelText: 'Primary Axis (A)'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: lengthB,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(labelText: 'Secondary Axis (B)'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: tolerance,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(labelText: 'Tolerance Threshold (%)'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: notes,
            maxLines: 2,
            decoration: const InputDecoration(labelText: 'Morphological Observations'),
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: brassEdge,
              foregroundColor: bgDark,
              minimumSize: const Size(double.infinity, 45),
            ),
            onPressed: () {
              try {
                final res = analyzePhi(
                  double.parse(lengthA.text.trim()),
                  double.parse(lengthB.text.trim()),
                  double.parse(tolerance.text.trim()),
                );
                setState(() {
                  phiResult = {
                    ...res,
                    'specimen': specimen.text.trim(),
                    'notes': notes.text.trim(),
                  };
                  phiError = null;
                });
              } catch (e) {
                setState(() {
                  phiResult = null;
                  phiError = 'Input Error: $e';
                });
              }
            },
            icon: const Icon(Icons.calculate),
            label: const Text('EXECUTE RATIO ANALYSIS', style: TextStyle(letterSpacing: 1.5)),
          ),
        ]),
        if (phiError != null)
          Text(phiError!, style: const TextStyle(color: Colors.redAccent)),
        if (phiResult != null)
          steampunkPanel('ANALYSIS RESULT', [
            Text(
              'Ratio (A/B): ${(phiResult!['ratio_long_short'] as double).toStringAsFixed(6)}',
              style: const TextStyle(fontSize: 22, color: vacuumCyan, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 6),
            Text('Target Phi: ${goldenRatio.toStringAsFixed(6)}'),
            Text('Relative Deviation: ${(phiResult!['relative_deviation_percent'] as double).toStringAsFixed(3)}%'),
            const SizedBox(height: 8),
            Text(
              phiResult!['within_tolerance'] ? 'COHERENCE MATCH CONFIRMED' : 'OUTSIDE TOLERANCE LIMITS',
              style: TextStyle(color: phiResult!['within_tolerance'] ? Colors.greenAccent : copperGlow),
            ),
          ]),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: panelBg,
        title: Row(
          children: [
            const Icon(Icons.token, color: copperGlow),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text(
                  'ESQET FIELD EXPLORER',
                  style: TextStyle(color: textGold, fontSize: 16, letterSpacing: 2.0, fontWeight: FontWeight.bold),
                ),
                Text(
                  'Unified Inverse Field Standard V2',
                  style: TextStyle(color: vacuumCyan, fontSize: 10, letterSpacing: 1.0),
                ),
              ],
            ),
          ],
        ),
      ),
      body: SafeArea(
        child: IndexedStack(
          index: page,
          children: [
            radarView(),
            phiLabView(),
          ],
        ),
      ),
      bottomNavigationBar: NavigationBar(
        backgroundColor: panelBg,
        indicatorColor: copperGlow.withAlpha(80),
        selectedIndex: page,
        onDestinationSelected: (v) => setState(() => page = v),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.radar, color: brassEdge),
            label: 'E8 Radar',
          ),
          NavigationDestination(
            icon: Icon(Icons.architecture, color: brassEdge),
            label: 'Phi Lab',
          ),
        ],
      ),
    );
  }
}

/// Steampunk Radar Custom Painter
class SteampunkRadarPainter extends CustomPainter {
  final double animationValue;
  final bool hasTarget;

  SteampunkRadarPainter({required this.animationValue, required this.hasTarget});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) / 2 - 10;

    final paintBrass = Paint()
      ..color = const Color(0xFFC5A059)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    final paintDim = Paint()
      ..color = const Color(0xFFC5A059).withAlpha(60)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;

    // Outer brass rings
    canvas.drawCircle(center, radius, paintBrass);
    canvas.drawCircle(center, radius * 0.66, paintDim);
    canvas.drawCircle(center, radius * 0.33, paintDim);

    // Crosshairs
    canvas.drawLine(Offset(center.dx - radius, center.dy), Offset(center.dx + radius, center.dy), paintDim);
    canvas.drawLine(Offset(center.dx, center.dy - radius), Offset(center.dx, center.dy + radius), paintDim);

    // Rotating Sweep Line
    final angle = animationValue * 2 * math.pi;
    final sweepPaint = Paint()
      ..color = vacuumCyan.withAlpha(180)
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;

    canvas.drawLine(
      center,
      Offset(center.dx + radius * math.cos(angle), center.dy + radius * math.sin(angle)),
      sweepPaint,
    );

    // Target Blip if computed
    if (hasTarget) {
      final targetPaint = Paint()
        ..color = copperGlow
        ..style = PaintingStyle.fill;
      canvas.drawCircle(Offset(center.dx + radius * 0.45, center.dy - radius * 0.35), 6, targetPaint);
    }
  }

  @override
  bool shouldRepaint(covariant SteampunkRadarPainter oldDelegate) {
    return oldDelegate.animationValue != animationValue || oldDelegate.hasTarget != hasTarget;
  }
}

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'phi.dart';

const accent = Color(0xFF61E5CB);
const copper = Color(0xFFF1B77A);
const surface = Color(0xFF15212C);

void main() {
  runApp(const FossilApp());
}

class FossilApp extends StatelessWidget {
  const FossilApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF091119),
        colorScheme: ColorScheme.fromSeed(
          seedColor: accent,
          brightness: Brightness.dark,
        ),
        inputDecorationTheme: const InputDecorationTheme(
          border: OutlineInputBorder(),
          filled: true,
        ),
      ),
      home: const FieldConsole(),
    );
  }
}

class FieldConsole extends StatefulWidget {
  const FieldConsole({super.key});

  @override
  State<FieldConsole> createState() => _FieldConsoleState();
}

class _FieldConsoleState extends State<FieldConsole> {
  final specimen = TextEditingController();
  final lengthA = TextEditingController();
  final lengthB = TextEditingController();
  final tolerance = TextEditingController(text: '2');
  final notes = TextEditingController();

  int page = 0;
  Map<String, dynamic>? result;
  String? error;

  @override
  void dispose() {
    for (final controller in [
      specimen,
      lengthA,
      lengthB,
      tolerance,
      notes,
    ]) {
      controller.dispose();
    }
    super.dispose();
  }

  void invalidate() {
    if (result != null || error != null) {
      setState(() {
        result = null;
        error = null;
      });
    }
  }

  void calculate() {
    try {
      final measurement = analyzePhi(
        double.parse(lengthA.text.trim()),
        double.parse(lengthB.text.trim()),
        double.parse(tolerance.text.trim()),
      );

      setState(() {
        result = {
          ...measurement,
          'specimen_id': specimen.text.trim(),
          'notes': notes.text.trim(),
          'timestamp': DateTime.now().toUtc().toIso8601String(),
          'units': 'Same units supplied by user',
        };
        error = null;
      });
    } catch (e) {
      setState(() {
        result = null;
        error = 'Check your inputs: $e';
      });
    }
  }

  Widget panel(String title, List<Widget> children) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: surface,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: accent.withAlpha(45)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              color: copper,
              fontSize: 15,
              letterSpacing: 1.5,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          ...children,
        ],
      ),
    );
  }

  Widget input(
    String label,
    TextEditingController controller, {
    bool numeric = false,
    int lines = 1,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: TextField(
        controller: controller,
        maxLines: lines,
        keyboardType: numeric
            ? const TextInputType.numberWithOptions(decimal: true)
            : TextInputType.text,
        decoration: InputDecoration(labelText: label),
        onChanged: (_) => invalidate(),
      ),
    );
  }

  Widget dashboard() {
    return ListView(
      padding: const EdgeInsets.all(18),
      children: [
        panel('FIELD OPERATIONS', [
          const Icon(Icons.radar, color: accent, size: 50),
          const SizedBox(height: 18),
          const Text(
            'Evidence first.
Interpretation second.',
            style: TextStyle(
              fontSize: 32,
              height: 1.15,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 18),
          const Text(
            'Specimen geometry, traceable measurements, '
            'and explicit uncertainty.',
          ),
          const SizedBox(height: 18),
          FilledButton.icon(
            onPressed: () => setState(() => page = 1),
            icon: const Icon(Icons.architecture),
            label: const Text('Open phi analysis'),
          ),
        ]),
        panel('MEASUREMENT STATUS', [
          const Text(
            'PHI CALCULATOR   /   AVAILABLE OFFLINE',
            style: TextStyle(color: accent),
          ),
          const SizedBox(height: 12),
          const Text(
            'Hardware telemetry is not connected in this frontend. '
            'No simulated readings or automatic PASS indicators.',
          ),
        ]),
      ],
    );
  }

  Widget phiLab() {
    final data = result;

    return ListView(
      padding: const EdgeInsets.all(18),
      children: [
        panel('PHI / GEOMETRY LAB', [
          input('Specimen ID', specimen),
          input('Length A', lengthA, numeric: true),
          input('Length B', lengthB, numeric: true),
          input('Tolerance (%)', tolerance, numeric: true),
          input('Landmark definitions / notes', notes, lines: 3),
          const Text(
            'Use the same units for both lengths. '
            'The longer length is divided by the shorter.',
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: calculate,
            icon: const Icon(Icons.calculate_outlined),
            label: const Text('Analyze ratio'),
          ),
        ]),
        if (error != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: Text(
              error!,
              style: const TextStyle(color: Colors.redAccent),
            ),
          ),
        if (data != null)
          panel('MEASUREMENT RESULT', [
            Text(
              (data['ratio_long_short'] as double).toStringAsFixed(8),
              style: const TextStyle(
                fontSize: 42,
                fontWeight: FontWeight.w800,
                color: accent,
              ),
            ),
            Text(
              'Reference phi: ${goldenRatio.toStringAsFixed(12)}',
            ),
            const SizedBox(height: 12),
            Text(
              'Relative deviation: '
              '${(data['relative_deviation_percent'] as double).toStringAsFixed(6)}%',
            ),
            const SizedBox(height: 8),
            Text(
              data['within_tolerance'] == true
                  ? 'WITHIN SELECTED TOLERANCE'
                  : 'OUTSIDE SELECTED TOLERANCE',
              style: const TextStyle(color: copper),
            ),
            const SizedBox(height: 14),
            const Text(
              'This is a numerical comparison, not a significance '
              'test, biological identification, or spiral fit.',
            ),
            const SizedBox(height: 14),
            OutlinedButton.icon(
              onPressed: () async {
                await Clipboard.setData(
                  ClipboardData(
                    text: const JsonEncoder.withIndent('  ').convert(data),
                  ),
                );

                if (!mounted) return;

                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Measurement JSON copied.'),
                  ),
                );
              },
              icon: const Icon(Icons.copy),
              label: const Text('Copy result JSON'),
            ),
            const SizedBox(height: 12),
            SelectableText(
              const JsonEncoder.withIndent('  ').convert(data),
              style: const TextStyle(fontSize: 12),
            ),
          ]),
      ],
    );
  }

  Widget hardware() {
    return ListView(
      padding: const EdgeInsets.all(18),
      children: [
        panel('INSTRUMENT INTEGRATION', [
          const Text(
            'This APK currently provides the local geometry interface. '
            'Your Python backend remains a separate Termux process.',
          ),
          const SizedBox(height: 16),
          const Text(
            'Camera landmark measurements: not included
'
            'Turntable control: not connected
'
            'Magnetometer: not connected to this UI
'
            'GPS heatmap: not connected
'
            'Sonar: not implemented
'
            'LiDAR layer rendering: not implemented',
          ),
        ]),
        panel('EXISTING BACKEND PREFLIGHT', [
          const Text('Run this separately in Termux:'),
          const SizedBox(height: 12),
          const SelectableText(
            'cd ~/Beta-Rocks
'
            'export PYTHONPATH="$PWD/src"
'
            'python3 -m fossil_scanner.cli preflight '
            '--work-dir "$HOME/fieldwork"',
          ),
        ]),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF091119),
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'FOSSILSCANNER',
              style: TextStyle(
                letterSpacing: 2.5,
                fontWeight: FontWeight.w800,
                fontSize: 19,
              ),
            ),
            Text(
              'FIELD CONSOLE / PHI LAB',
              style: TextStyle(
                fontSize: 10,
                letterSpacing: 2,
                color: copper,
              ),
            ),
          ],
        ),
      ),
      body: SafeArea(
        child: IndexedStack(
          index: page,
          children: [
            dashboard(),
            phiLab(),
            hardware(),
          ],
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: page,
        onDestinationSelected: (value) {
          setState(() => page = value);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.radar),
            label: 'Field',
          ),
          NavigationDestination(
            icon: Icon(Icons.architecture),
            label: 'Phi lab',
          ),
          NavigationDestination(
            icon: Icon(Icons.sensors),
            label: 'Hardware',
          ),
        ],
      ),
    );
  }
}

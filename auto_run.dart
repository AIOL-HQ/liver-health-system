import 'dart:io';

Future<void> runStep(String title, String executable, List<String> args, {bool shell = false}) async {
  stdout.writeln('\n$title');
  final process = await Process.start(
    executable,
    args,
    runInShell: true,
    mode: ProcessStartMode.inheritStdio,
    workingDirectory: Directory.current.path,
  );
  final code = await process.exitCode;
  if (code != 0) {
    stderr.writeln('Failed at step: $title (exit code $code)');
    exit(code);
  }
}

Future<void> main() async {
  stdout.writeln('Liver Health Smart System - Dart launcher');
  stdout.writeln('Working directory: ${Directory.current.path}');

  final isWindows = Platform.isWindows;
  if (!isWindows) {
    stdout.writeln('This launcher was prepared mainly for Windows. You can still run:');
    stdout.writeln('python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python app.py');
    return;
  }

  final venvDir = Directory('venv');
  if (!venvDir.existsSync()) {
    try {
      await runStep('[1/4] Creating venv...', 'py', ['-m', 'venv', 'venv']);
    } catch (_) {
      await runStep('[1/4] Creating venv...', 'python', ['-m', 'venv', 'venv']);
    }
  }

  await runStep('[2/4] Upgrading pip...', r'venv\Scripts\python.exe', ['-m', 'pip', 'install', '--upgrade', 'pip']);
  await runStep('[3/4] Installing requirements...', r'venv\Scripts\python.exe', ['-m', 'pip', 'install', '-r', 'requirements.txt']);

  if (Platform.isWindows) {
    Process.start('cmd', ['/c', 'start', 'http://127.0.0.1:5000'], runInShell: true);
  }

  await runStep('[4/4] Running Flask app...', r'venv\Scripts\python.exe', ['app.py']);
}

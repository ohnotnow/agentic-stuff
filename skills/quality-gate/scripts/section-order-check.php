#!/usr/bin/env php
<?php

/**
 * Section-order checker for Eloquent models and Livewire components.
 *
 * Checks that class members appear in our conventional section order:
 *
 *   Models:   lifecycle (boot/booted/casts) -> relationships -> scopes
 *             -> accessors/mutators -> custom methods
 *   Livewire: mount() -> render() -> lifecycle hooks (updatedFoo etc.)
 *             -> custom methods
 *
 * Usage:
 *   php section-order-check.php /path/to/laravel-repo [extra-class-file.php ...] [--cap=5]
 *
 * The repo must have vendor/ installed (classes are inspected via reflection
 * using the repo's own autoloader). Extra positional .php files are included
 * directly and any classes they declare are checked too - useful for fixtures.
 *
 * There is deliberately NO error handling around class loading. If a class
 * can't load (missing parent, absent package), the scan dies loudly with PHP's
 * error naming the class - a class that can't even load is the most urgent
 * finding a review can produce, not something to skip past. Deal with the
 * corpse, re-run.
 *
 * Report-only; never edits anything. Detailed output is capped to the worst
 * --cap files (default 5) so grotty codebases get a workable worst-offenders
 * list rather than a wall of noise: fix, re-run, repeat.
 *
 * Known limitations (deliberate):
 *  - Model methods with no return type that aren't name-classifiable (old-style
 *    untyped relationships) are skipped, not guessed at. They're reported as a
 *    count so the omission is visible.
 *  - Property ordering isn't checked (PHP reflection has no property line numbers).
 *  - Livewire single-file/view-first components aren't seen (class-based only).
 *
 * Exit codes: 0 = clean, 1 = violations found, 2 = usage/setup error.
 */

const MODEL_SECTIONS = ['lifecycle', 'relationships', 'scopes', 'accessors', 'custom methods'];
const LIVEWIRE_SECTIONS = ['mount()', 'render()', 'lifecycle hooks', 'custom methods'];

$cap = 5;
$paths = [];
foreach (array_slice($argv, 1) as $arg) {
    if (preg_match('/^--cap=(\d+)$/', $arg, $m)) {
        $cap = (int) $m[1];
        continue;
    }
    $paths[] = $arg;
}

$repo = array_shift($paths);
if ($repo === null || ! is_dir($repo)) {
    fwrite(STDERR, "Usage: php section-order-check.php /path/to/laravel-repo [fixture.php ...] [--cap=5]\n");
    exit(2);
}

$autoload = $repo.'/vendor/autoload.php';
if (! file_exists($autoload)) {
    fwrite(STDERR, "No vendor/autoload.php in {$repo} - run composer install first.\n");
    exit(2);
}
require $autoload;

// Collect candidate classes: PSR-4 map of app/ => App\ ...
$classes = [];
$appDir = realpath($repo.'/app');
if ($appDir !== false) {
    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($appDir, FilesystemIterator::SKIP_DOTS)
    );
    foreach ($iterator as $file) {
        if ($file->getExtension() !== 'php') {
            continue;
        }
        $relative = substr($file->getPathname(), strlen($appDir) + 1, -4);
        $classes['App\\'.str_replace(DIRECTORY_SEPARATOR, '\\', $relative)] = $file->getPathname();
    }
}

// ... plus any explicitly passed fixture files.
foreach ($paths as $fixture) {
    if (! file_exists($fixture)) {
        fwrite(STDERR, "Fixture file not found: {$fixture}\n");
        exit(2);
    }
    $declaredBefore = get_declared_classes();
    require_once $fixture;
    foreach (array_diff(get_declared_classes(), $declaredBefore) as $newClass) {
        $classes[$newClass] = realpath($fixture);
    }
}

/**
 * @return int|string|null rank, 'unclassifiable', or null to silently skip
 */
function classifyModelMethod(ReflectionMethod $method): int|string|null
{
    $name = $method->getName();

    if (str_starts_with($name, '__')) {
        return null; // magic methods sit outside the convention
    }
    if (in_array($name, ['boot', 'booted', 'booting', 'casts', 'newFactory'], true)) {
        return 0; // lifecycle / boilerplate
    }
    if (preg_match('/^scope[A-Z]/', $name)) {
        return 2;
    }
    foreach ($method->getAttributes() as $attribute) {
        if ($attribute->getName() === 'Illuminate\\Database\\Eloquent\\Attributes\\Scope') {
            return 2;
        }
    }
    if (preg_match('/^(get|set)[A-Z].*Attribute$/', $name)) {
        return 3;
    }

    $type = $method->getReturnType();
    if ($type instanceof ReflectionNamedType && ! $type->isBuiltin()) {
        if ($type->getName() === 'Illuminate\\Database\\Eloquent\\Casts\\Attribute') {
            return 3;
        }
        if (is_a($type->getName(), 'Illuminate\\Database\\Eloquent\\Relations\\Relation', true)) {
            return 1;
        }
    }
    if ($type === null) {
        return 'unclassifiable'; // could be an untyped relationship - don't guess
    }

    return 4; // custom methods
}

function classifyLivewireMethod(ReflectionMethod $method): ?int
{
    $name = $method->getName();

    if (str_starts_with($name, '__')) {
        return null;
    }
    if ($name === 'mount') {
        return 0;
    }
    if ($name === 'render') {
        return 1;
    }
    if (preg_match('/^(boot|booted|hydrate|dehydrate|updating|updated|rendering|rendered|exception)([A-Z].*)?$/', $name)) {
        return 2;
    }

    return 3; // custom methods
}

$fileReports = [];      // file => list of violation strings
$unclassifiable = [];   // file => count
$modelCount = 0;
$livewireCount = 0;

foreach ($classes as $class => $file) {
    if (! class_exists($class)) {
        continue; // file declares no such class (helpers etc.)
    }
    $reflection = new ReflectionClass($class);
    if ($reflection->isAbstract() || $reflection->isInterface()) {
        continue;
    }

    if ($reflection->isSubclassOf('Illuminate\\Database\\Eloquent\\Model')) {
        $kind = 'model';
        $sections = MODEL_SECTIONS;
        $modelCount++;
    } elseif (class_exists('Livewire\\Component') && $reflection->isSubclassOf('Livewire\\Component')) {
        $kind = 'livewire';
        $sections = LIVEWIRE_SECTIONS;
        $livewireCount++;
    } else {
        continue;
    }

    $ranked = [];
    foreach ($reflection->getMethods() as $method) {
        if ($method->getFileName() !== $reflection->getFileName()) {
            continue; // trait methods live in the trait's file
        }
        if ($method->getDeclaringClass()->getName() !== $class) {
            continue; // inherited
        }
        $rank = $kind === 'model' ? classifyModelMethod($method) : classifyLivewireMethod($method);
        if ($rank === 'unclassifiable') {
            $unclassifiable[$file] = ($unclassifiable[$file] ?? 0) + 1;
            continue;
        }
        if ($rank === null) {
            continue;
        }
        $ranked[] = ['line' => $method->getStartLine(), 'rank' => $rank, 'name' => $method->getName()];
    }

    usort($ranked, fn (array $a, array $b): int => $a['line'] <=> $b['line']);

    $highest = null;
    foreach ($ranked as $entry) {
        if ($highest !== null && $entry['rank'] < $highest['rank']) {
            $fileReports[$file][] = sprintf(
                'line %d: %s() [%s] appears after %s() [%s] at line %d',
                $entry['line'], $entry['name'], $sections[$entry['rank']],
                $highest['name'], $sections[$highest['rank']], $highest['line'],
            );
            continue; // don't ratchet up from a misplaced method
        }
        $highest = $entry;
    }
}

// ---- report ----
$totalViolations = array_sum(array_map('count', $fileReports));
printf(
    "Section order check: %d models, %d Livewire components inspected in %s\n",
    $modelCount, $livewireCount, $repo,
);
printf("Expected model order:    %s\n", implode(' -> ', MODEL_SECTIONS));
printf("Expected Livewire order: %s\n\n", implode(' -> ', LIVEWIRE_SECTIONS));

if ($totalViolations === 0) {
    echo "OK: no section-order violations found.\n";
} else {
    uasort($fileReports, fn (array $a, array $b): int => count($b) <=> count($a));
    $detailed = array_slice($fileReports, 0, $cap, preserve_keys: true);
    foreach ($detailed as $file => $violations) {
        printf("%s - %d violation%s\n", $file, count($violations), count($violations) === 1 ? '' : 's');
        foreach ($violations as $violation) {
            echo '   '.$violation."\n";
        }
    }
    $remaining = array_slice($fileReports, $cap, preserve_keys: true);
    if ($remaining !== []) {
        printf("\n+ %d more file%s with violations (re-run after fixing the above, or raise --cap):\n", count($remaining), count($remaining) === 1 ? '' : 's');
        foreach ($remaining as $file => $violations) {
            printf("   %s (%d)\n", $file, count($violations));
        }
    }
    printf("\nFAIL: %d violation%s in %d file%s.\n", $totalViolations, $totalViolations === 1 ? '' : 's', count($fileReports), count($fileReports) === 1 ? '' : 's');
}

if ($unclassifiable !== []) {
    printf(
        "\nNote: %d method%s across %d file%s skipped as unclassifiable (no return type - possibly untyped relationships). Order not checked for those.\n",
        array_sum($unclassifiable), array_sum($unclassifiable) === 1 ? '' : 's',
        count($unclassifiable), count($unclassifiable) === 1 ? '' : 's',
    );
}

exit($totalViolations === 0 ? 0 : 1);

rootProject.name = "Abgaben"

val submissionsDir = file("repos").absolutePath

// Dynamically include subprojects for each student and their exercises
val studentDirs = file(submissionsDir).listFiles()?.filter { it.isDirectory } ?: emptyList()

studentDirs.forEach { studentDir ->
    studentDir.listFiles()?.filter { it.isDirectory }?.forEach { exerciseDir ->
        val projectPath = "repos:${studentDir.name}:${exerciseDir.name}"
        include(projectPath)
        // findProject(projectPath)?.projectDir = exerciseDir
    }
}

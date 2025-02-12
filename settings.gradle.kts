rootProject.name = "Submissions"

// Dynamically include subprojects for each student and their exercises
// Structure is baseDir/assignmentDir/submissionDir

// Set the base dir for cloning submissions into
val baseDir = file("repos")

// Find the assignment directories in the baseDir
val assignmentDirs = file(baseDir).listFiles()?.filter { it.isDirectory } ?: emptyList()

// Find the submissions and include them as subprojects
assignmentDirs.forEach { assignmentDir ->
    assignmentDir.listFiles()?.filter { it.isDirectory }?.forEach { submissionDir ->
        val projectPath = "${baseDir.name}:${assignmentDir.name}:${submissionDir.name}"
        include(projectPath)
        // this would change the project dir -> could be used for ditching the base dir prefix (e.g. "repos:[...]")
        // findProject(projectPath)?.projectDir = submissionDir
    }
}

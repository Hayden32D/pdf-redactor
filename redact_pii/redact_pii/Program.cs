using System.Diagnostics;
using System;


string pythonPath = @"C:\Users\HDouglas\AppData\Local\Programs\Python\Python311\python.exe"; //replace with your path
string scriptPath = @"C:\Users\HDouglas\OneDrive - Method Automation Services Inc\Documents\Summer 2025\C# Code\Pii Python\pii.py"; //replace with your path
string pdfFolder = @"C:\Users\HDouglas\OneDrive - Method Automation Services Inc\Documents\Summer 2025\C# Code\Pii Python\pdfs"; //folders name for pdfs stored
string folderArgs = $"\"{scriptPath}\" \"{pdfFolder}\"";

ProcessStartInfo psi = new ProcessStartInfo
{
    FileName = pythonPath,
    Arguments = folderArgs,
    UseShellExecute = false,
    RedirectStandardOutput = true,
    RedirectStandardError = true,
    CreateNoWindow = true
};

using (Process process = Process.Start(psi))
{
    string output = process.StandardOutput.ReadToEnd();
    string errors = process.StandardError.ReadToEnd();

    process.WaitForExit();

    // Show Python output
    Console.WriteLine("Output:\n" + output);

    // Show any errors
    if (!string.IsNullOrEmpty(errors))
    {
        Console.WriteLine("Errors:\n" + errors);
    }
}

Console.WriteLine("Done processing PDFs.");
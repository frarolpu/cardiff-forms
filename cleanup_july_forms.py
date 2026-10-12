#!/usr/bin/env python3
"""
Script para analizar y borrar formularios de julio (202607XX) de saved_forms/
Primero informa sin borrar, luego después de confirmación borra y compara espacio
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def get_directory_size(directory):
    """Calcula tamaño total en bytes de un directorio"""
    total_size = 0
    if Path(directory).exists():
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    return total_size

def format_size(size_bytes):
    """Convierte bytes a formato legible (KB, MB, GB)"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def find_july_forms(saved_forms_dir='saved_forms'):
    """Encuentra todos los formularios de julio (202607XX)"""
    july_forms = []
    saved_forms_path = Path(saved_forms_dir)
    
    if not saved_forms_path.exists():
        print(f"❌ Directorio '{saved_forms_dir}' no existe")
        return july_forms
    
    # Buscar archivos con 202607 en el nombre
    for file in saved_forms_path.glob('*202607*'):
        if file.is_file():
            july_forms.append(file)
    
    return sorted(july_forms)

def analyze_cleanup(saved_forms_dir='saved_forms'):
    """Analiza qué se va a borrar sin borrar nada"""
    print("=" * 70)
    print("📊 ANÁLISIS DE LIMPIEZA - Formularios de Julio (202607XX)")
    print("=" * 70)
    print()
    
    # Medir espacio ANTES
    print("📏 Espacio ocupado ANTES de limpieza:")
    size_before = get_directory_size(saved_forms_dir)
    print(f"   Total en saved_forms/: {format_size(size_before)}")
    print()
    
    # Encontrar formularios de julio
    july_files = find_july_forms(saved_forms_dir)
    
    if not july_files:
        print("✅ No se encontraron formularios de julio (202607XX)")
        print()
        return None
    
    # Calcular estadísticas
    print(f"📋 Formularios encontrados con 202607XX: {len(july_files)}")
    print()
    
    # Agrupar por formulario (base name sin extensión)
    forms_dict = {}
    total_size_to_delete = 0
    
    for file in july_files:
        # Extraer base name (sin .pdf/.json)
        base_name = file.name
        if base_name.endswith(('.pdf', '.json')):
            base_name = base_name.rsplit('.', 1)[0]
        
        if base_name not in forms_dict:
            forms_dict[base_name] = []
        
        file_size = file.stat().st_size
        forms_dict[base_name].append({
            'path': file,
            'name': file.name,
            'size': file_size
        })
        total_size_to_delete += file_size
    
    # Mostrar detalle
    print("📄 Detalle de archivos a borrar:")
    print()
    for base_name in sorted(forms_dict.keys()):
        files = forms_dict[base_name]
        print(f"  {base_name}")
        for file_info in sorted(files, key=lambda x: x['name']):
            print(f"    - {file_info['name']:<50} {format_size(file_info['size']):>12}")
    
    print()
    print("=" * 70)
    print(f"📊 RESUMEN:")
    print(f"   Formularios (pares PDF+JSON): {len(forms_dict)}")
    print(f"   Archivos totales a borrar:    {len(july_files)}")
    print(f"   Espacio a liberar:            {format_size(total_size_to_delete)}")
    print()
    
    return {
        'files': july_files,
        'count': len(july_files),
        'size_to_delete': total_size_to_delete,
        'size_before': size_before
    }

def execute_cleanup(cleanup_info, saved_forms_dir='saved_forms'):
    """Ejecuta la limpieza después de confirmación"""
    if cleanup_info is None:
        return
    
    print()
    confirm = input("⚠️  ¿Estás completamente seguro de que quieres borrar estos archivos? (escribe 'SÍ' para confirmar): ")
    
    if confirm.lower() != 'sí' and confirm.lower() != 'si':
        print("❌ Operación cancelada. No se borró nada.")
        return
    
    print()
    print("🗑️  Borrando archivos...")
    print()
    
    deleted_count = 0
    deleted_size = 0
    errors = []
    
    for file in cleanup_info['files']:
        try:
            file_size = file.stat().st_size
            file.unlink()  # Borrar
            deleted_count += 1
            deleted_size += file_size
            print(f"  ✅ Borrado: {file.name}")
        except Exception as e:
            errors.append(f"  ❌ Error al borrar {file.name}: {str(e)}")
    
    if errors:
        print()
        for error in errors:
            print(error)
    
    print()
    print("=" * 70)
    print("📊 RESULTADO DE LA LIMPIEZA:")
    print("=" * 70)
    print(f"   Archivos borrados: {deleted_count}")
    print(f"   Espacio liberado:  {format_size(deleted_size)}")
    print()
    
    # Medir espacio DESPUÉS
    size_after = get_directory_size(saved_forms_dir)
    size_freed = cleanup_info['size_before'] - size_after
    
    print("📏 Comparativa de espacio:")
    print(f"   Antes:  {format_size(cleanup_info['size_before'])}")
    print(f"   Después: {format_size(size_after)}")
    print(f"   Liberado: {format_size(size_freed)} ({(size_freed/cleanup_info['size_before']*100):.1f}%)")
    print()
    print("=" * 70)

if __name__ == '__main__':
    # Fase 1: Análisis sin borrar
    cleanup_info = analyze_cleanup()
    
    # Fase 2: Si hay archivos, ejecutar limpieza con confirmación
    if cleanup_info and cleanup_info['files']:
        execute_cleanup(cleanup_info)
    
    print("✅ Script completado.")

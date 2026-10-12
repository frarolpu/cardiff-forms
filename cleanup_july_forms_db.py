#!/usr/bin/env python3
"""
Script para analizar y borrar formularios de julio (202607XX) de la BD PostgreSQL
Primero informa sin borrar, luego después de confirmación borra y compara espacio
Uso en Render: DATABASE_URL=<url> python cleanup_july_forms_db.py
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from urllib.parse import urlparse

def parse_database_url(db_url):
    """Parsea DATABASE_URL de Render a componentes"""
    parsed = urlparse(db_url)
    return {
        'host': parsed.hostname,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/'),
        'port': parsed.port or 5432
    }

def format_size(size_bytes):
    """Convierte bytes a formato legible"""
    if size_bytes is None:
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_db_connection(db_url):
    """Conecta a la base de datos PostgreSQL"""
    config = parse_database_url(db_url)
    try:
        conn = psycopg2.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            port=config['port']
        )
        return conn
    except Exception as e:
        print(f"❌ Error conectando a BD: {str(e)}")
        return None

def get_table_size(conn, table_name='saved_forms'):
    """Obtiene el tamaño total de una tabla en bytes"""
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT pg_total_relation_size('{table_name}'::regclass) as size
            """)
            result = cur.fetchone()
            return result['size'] if result else 0
    except Exception as e:
        print(f"⚠️  Advertencia al obtener tamaño: {str(e)}")
        return 0

def find_july_forms_db(conn):
    """Encuentra todos los formularios de julio en la BD"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, filename, section, status, created_at, 
                       octet_length(pdf_data) as pdf_size
                FROM saved_forms
                WHERE filename LIKE '%202607%'
                ORDER BY created_at DESC
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"❌ Error buscando registros: {str(e)}")
        print(f"   Query: SELECT id, filename, section, status, created_at, octet_length(pdf_data) as pdf_size FROM saved_forms WHERE filename LIKE '%202607%'")
        return []

def analyze_cleanup_db(db_url):
    """Analiza qué se va a borrar sin borrar nada"""
    print("=" * 80)
    print("📊 ANÁLISIS DE LIMPIEZA - Formularios de Julio (202607XX) EN BASE DE DATOS")
    print("=" * 80)
    print()
    
    # Conectar a BD
    conn = get_db_connection(db_url)
    if not conn:
        return None
    
    try:
        # Tamaño ANTES
        print("📏 Espacio ocupado ANTES de limpieza:")
        size_before = get_table_size(conn)
        print(f"   Tabla saved_forms: {format_size(size_before)}")
        print()
        
        # Encontrar formularios de julio
        july_records = find_july_forms_db(conn)
        
        if not july_records:
            print("✅ No se encontraron formularios de julio (202607XX) en la BD")
            print()
            return None
        
        # Calcular estadísticas
        print(f"📋 Registros encontrados con 202607XX: {len(july_records)}")
        print()
        
        # Agrupar por formulario
        forms_dict = {}
        total_size = 0
        
        for record in july_records:
            section = record['section']
            if section not in forms_dict:
                forms_dict[section] = []
            
            pdf_size = record['pdf_size'] or 0
            record_size = pdf_size
            
            forms_dict[section].append({
                'id': record['id'],
                'filename': record['filename'],
                'status': record['status'],
                'created_at': record['created_at'],
                'pdf_size': pdf_size,
                'total_size': record_size
            })
            total_size += record_size
        
        # Mostrar detalle
        print("📄 Detalle de registros a borrar:")
        print()
        for section in sorted(forms_dict.keys()):
            records = forms_dict[section]
            print(f"  Sección: {section} ({len(records)} registros)")
            for rec in records:
                print(f"    ID {rec['id']}: {rec['filename']}")
                print(f"              Tamaño PDF: {format_size(rec['pdf_size'])}")
                print(f"              Estado: {rec['status']} | Fecha: {rec['created_at']}")
        
        print()
        print("=" * 80)
        print(f"📊 RESUMEN:")
        print(f"   Secciones: {len(forms_dict)}")
        print(f"   Registros totales a borrar: {len(july_records)}")
        print(f"   Espacio ocupado por estos registros: {format_size(total_size)}")
        print(f"   Porcentaje de la tabla: {(total_size/size_before*100):.1f}% " if size_before > 0 else "")
        print()
        
        return {
            'records': july_records,
            'count': len(july_records),
            'size_to_delete': total_size,
            'size_before': size_before,
            'connection': conn
        }
    
    finally:
        if conn:
            conn.close()

def execute_cleanup_db(cleanup_info, db_url):
    """Ejecuta la limpieza después de confirmación"""
    if cleanup_info is None:
        return
    
    print()
    confirm = input("⚠️  ¿Estás COMPLETAMENTE seguro de que quieres borrar estos registros? (escribe 'SÍ' para confirmar): ")
    
    if confirm.lower() not in ['sí', 'si']:
        print("❌ Operación cancelada. No se borró nada.")
        return
    
    print()
    print("🗑️  Borrando registros de la base de datos...")
    print()
    
    # Conectar de nuevo para borrar
    conn = get_db_connection(db_url)
    if not conn:
        print("❌ No se pudo conectar a la base de datos")
        return
    
    try:
        deleted_count = 0
        errors = []
        
        with conn.cursor() as cur:
            for record in cleanup_info['records']:
                try:
                    cur.execute("DELETE FROM saved_forms WHERE id = %s", (record['id'],))
                    deleted_count += 1
                    print(f"  ✅ Borrado: ID {record['id']} - {record['filename']}")
                except Exception as e:
                    errors.append(f"  ❌ Error borrando ID {record['id']}: {str(e)}")
        
        # Commit de todos los cambios
        conn.commit()
        
        if errors:
            print()
            for error in errors:
                print(error)
        
        print()
        print("=" * 80)
        print("📊 RESULTADO DE LA LIMPIEZA:")
        print("=" * 80)
        print(f"   Registros borrados: {deleted_count} de {len(cleanup_info['records'])}")
        print()
        
        # Medir espacio DESPUÉS
        size_after = get_table_size(conn)
        size_freed = cleanup_info['size_before'] - size_after
        
        print("📏 Comparativa de espacio:")
        print(f"   Antes:    {format_size(cleanup_info['size_before'])}")
        print(f"   Después:  {format_size(size_after)}")
        print(f"   Liberado: {format_size(size_freed)} ({(size_freed/cleanup_info['size_before']*100):.1f}%)")
        print()
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error durante la limpieza: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    # Obtener DATABASE_URL de variables de entorno o parámetro
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url and len(sys.argv) > 1:
        db_url = sys.argv[1]
    
    if not db_url:
        print("❌ DATABASE_URL no proporcionada.")
        print()
        print("Uso:")
        print("  1. Con variable de entorno: export DATABASE_URL='...' && python cleanup_july_forms_db.py")
        print("  2. Con parámetro: python cleanup_july_forms_db.py 'postgresql://...'")
        sys.exit(1)
    
    # Fase 1: Análisis sin borrar
    print()
    cleanup_info = analyze_cleanup_db(db_url)
    
    # Fase 2: Si hay registros, ejecutar limpieza con confirmación
    if cleanup_info and cleanup_info['records']:
        execute_cleanup_db(cleanup_info, db_url)
    
    print("✅ Script completado.")
    print()

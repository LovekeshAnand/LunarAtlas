r"""
Script to crawl the ch3_libs directory structure and insert observation data
directly into the LunarAtlas PostgreSQL database.

Database: LunarAtlas
Table: observation
Foreign Key: session_id → observation_session table

This script will:
1. Crawl all date folders and observation folders
2. Extract metadata from XML files
3. Generate new observation IDs based on timestamps
4. Verify foreign key constraints (session_id)
5. Insert data into the database
6. Provide detailed logging and error handling
"""

import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2 import Error, extras
import logging

class ObservationDatabaseInserter:
    """Crawls directory structure and inserts observations into PostgreSQL database."""
    
    def __init__(self, base_path: str, db_config: Dict):
        """
        Initialize the inserter.
        
        Args:
            base_path: Base path to the calibrated data directory
            db_config: Database configuration dictionary with keys:
                      host, database, user, password, port (optional, default 5432)
        """
        self.base_path = Path(base_path)
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        self.observations = []
        self.existing_sessions = set()
        self.stats = {
            'total_found': 0,
            'inserted': 0,
            'skipped': 0,
            'errors': 0,
            'sessions_created': 0
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('observation_db_insert.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def connect_to_database(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Connecting to PostgreSQL database: {self.db_config['database']} @ {self.db_config['host']}")
            
            self.connection = psycopg2.connect(
                host=self.db_config['host'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                port=self.db_config.get('port', 5432)
            )
            
            self.cursor = self.connection.cursor()
            
            # Get PostgreSQL version
            self.cursor.execute("SELECT version();")
            db_version = self.cursor.fetchone()[0]
            self.logger.info(f"Successfully connected to PostgreSQL: {db_version}")
            
            # Verify table exists
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'observation'
                );
            """)
            
            if not self.cursor.fetchone()[0]:
                self.logger.error("Table 'observation' does not exist in database!")
                return False
            
            # Verify observation_session table exists
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'observation_session'
                );
            """)
            
            if not self.cursor.fetchone()[0]:
                self.logger.error("Table 'observation_session' does not exist in database!")
                return False
            
            return True
            
        except Error as e:
            self.logger.error(f"Error connecting to PostgreSQL Database: {e}")
            return False
    
    def disconnect_from_database(self):
        """Close database connection."""
        if self.connection:
            if self.cursor:
                self.cursor.close()
            self.connection.close()
            self.logger.info("Database connection closed")
    
    def load_existing_sessions(self) -> bool:
        """
        Load existing session_ids from observation_session table.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Loading existing sessions from observation_session table...")
            
            self.cursor.execute("SELECT session_id FROM observation_session")
            sessions = self.cursor.fetchall()
            
            self.existing_sessions = {session[0] for session in sessions}
            self.logger.info(f"Found {len(self.existing_sessions)} existing sessions")
            
            if self.existing_sessions:
                self.logger.info(f"Sample sessions: {list(self.existing_sessions)[:3]}")
            
            return True
            
        except Error as e:
            self.logger.error(f"Error loading existing sessions: {e}")
            return False
    
    def verify_session_exists(self, session_id: str) -> bool:
        """
        Check if a session_id exists in observation_session table.
        
        Args:
            session_id: Session ID to verify
            
        Returns:
            True if exists, False otherwise
        """
        return session_id in self.existing_sessions
    
    def create_missing_session(self, session_id: str, date_folder: str) -> bool:
        """
        Create a missing session in observation_session table.
        
        Args:
            session_id: Session ID to create (e.g., 'CH3 LIBS v2 20230825')
            date_folder: Date folder name (YYYYMMDD)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse date from folder name
            observation_date = datetime.strptime(date_folder, '%Y%m%d').date()
            
            # Insert into observation_session
            insert_query = """
                INSERT INTO observation_session 
                (session_id, dataset_version_id, observation_date, date_folder, target_description, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_id) DO NOTHING
            """
            
            values = (
                session_id,
                'lib-v2',  # dataset_version_id
                observation_date,
                date_folder,
                None,  # target_description
                f"Auto-created session for {date_folder}"
            )
            
            self.cursor.execute(insert_query, values)
            self.connection.commit()
            
            # Add to existing sessions set
            self.existing_sessions.add(session_id)
            self.stats['sessions_created'] += 1
            
            self.logger.info(f"Created new session: {session_id}")
            return True
            
        except Error as e:
            self.logger.error(f"Error creating session {session_id}: {e}")
            self.connection.rollback()
            return False
    
    def generate_observation_id(self, observation_code: str) -> Optional[str]:
        """Generate new observation ID from observation code."""
        pattern = r'ch3_lib_(\d{3})_(\d{8})T(\d{6})_(\d{2})_l1'
        match = re.match(pattern, observation_code)
        
        if match:
            date = match.group(2)
            time = match.group(3)
            sub_idx = match.group(4)
            return f"LIB-{date}-{time}-{sub_idx}"
        
        return None
    
    def parse_xml_metadata(self, xml_path: Path) -> Dict:
        """
        Parse XML file to extract metadata.
        
        Args:
            xml_path: Path to the XML file
            
        Returns:
            Dictionary containing metadata
        """
        metadata = {
            'start_time': None,
            'stop_time': None,
            'pds_version_id': '1.0',
            'information_model_version': '1.11.0.0',
            'processing_level': 'Calibrated',
            'purpose': 'Science'
        }
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            for elem in root.iter():
                tag = elem.tag.split('}')[-1]  # Remove namespace
                
                if tag == 'start_date_time':
                    metadata['start_time'] = elem.text
                elif tag == 'stop_date_time':
                    metadata['stop_time'] = elem.text
                elif tag == 'version_id':
                    metadata['pds_version_id'] = elem.text
                elif tag == 'information_model_version':
                    metadata['information_model_version'] = elem.text
                    
        except Exception as e:
            self.logger.warning(f"Could not parse XML {xml_path}: {e}")
            
        return metadata
    
    def extract_sequence_number(self, observation_code: str) -> Optional[int]:
        """Extract sequence number from observation code."""
        pattern = r'ch3_lib_(\d{3})_'
        match = re.search(pattern, observation_code)
        return int(match.group(1)) if match else None
    
    def extract_sub_index(self, observation_code: str) -> Optional[int]:
        """Extract sub-index from observation code."""
        pattern = r'T\d{6}_(\d{2})_l1'
        match = re.search(pattern, observation_code)
        return int(match.group(1)) if match else None
    
    def generate_session_id(self, date_folder: str) -> str:
        """Generate session ID from date folder."""
        return f"CH3 LIBS v2 {date_folder}"
    
    def generate_logical_identifier(self, observation_code: str) -> str:
        """Generate logical identifier (URN)."""
        return f"urn:isro:isda:ch3_chr.lib:data_calibrated:{observation_code}"
    
    def check_observation_exists(self, observation_id: str) -> bool:
        """
        Check if observation_id already exists in database.
        
        Args:
            observation_id: Observation ID to check
            
        Returns:
            True if exists, False otherwise
        """
        try:
            self.cursor.execute(
                "SELECT COUNT(*) FROM observation WHERE observation_id = %s",
                (observation_id,)
            )
            count = self.cursor.fetchone()[0]
            return count > 0
        except Error as e:
            self.logger.error(f"Error checking if observation exists: {e}")
            return False
    
    def insert_observation(self, observation: Dict) -> bool:
        """
        Insert a single observation into the database.
        
        Args:
            observation: Dictionary containing observation data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if already exists
            if self.check_observation_exists(observation['observation_id']):
                self.logger.warning(f"Observation {observation['observation_id']} already exists, skipping")
                self.stats['skipped'] += 1
                return False
            
            # Verify session exists
            if not self.verify_session_exists(observation['session_id']):
                self.logger.warning(f"Session {observation['session_id']} does not exist, creating it...")
                # Extract date from observation_id
                date_match = re.search(r'LIB-(\d{8})-', observation['observation_id'])
                if date_match:
                    date_folder = date_match.group(1)
                    if not self.create_missing_session(observation['session_id'], date_folder):
                        self.logger.error(f"Failed to create session {observation['session_id']}")
                        self.stats['errors'] += 1
                        return False
            
            # Insert observation
            insert_query = """
                INSERT INTO observation (
                    observation_id, session_id, logical_identifier,
                    observation_code, observation_number, sub_index,
                    start_time, stop_time, pds_version_id,
                    information_model_version, processing_level, purpose
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                observation['observation_id'],
                observation['session_id'],
                observation['logical_identifier'],
                observation['observation_code'],
                observation['observation_number'],
                observation['sub_index'],
                observation['start_time'],
                observation['stop_time'],
                observation['pds_version_id'],
                observation['information_model_version'],
                observation['processing_level'],
                observation['purpose']
            )
            
            self.cursor.execute(insert_query, values)
            self.connection.commit()
            
            self.stats['inserted'] += 1
            self.logger.info(f"✓ Inserted observation: {observation['observation_id']}")
            return True
            
        except Error as e:
            self.logger.error(f"Error inserting observation {observation['observation_id']}: {e}")
            self.connection.rollback()
            self.stats['errors'] += 1
            return False
    
    def crawl_and_insert(self, batch_size: int = 1, auto_create_sessions: bool = True) -> int:
        """
        Crawl directory structure and insert observations into database.
        
        Args:
            batch_size: Number of observations to insert before committing (1 = commit each)
            auto_create_sessions: Automatically create missing sessions
            
        Returns:
            Number of observations successfully inserted
        """
        self.logger.info(f"Starting crawl of directory: {self.base_path}")
        self.logger.info("="*70)
        
        if not self.base_path.exists():
            self.logger.error(f"Directory not found: {self.base_path}")
            return 0
        
        # Get all date folders
        date_folders = sorted([d for d in self.base_path.iterdir() 
                              if d.is_dir() and re.match(r'^\d{8}$', d.name)])
        
        self.logger.info(f"Found {len(date_folders)} date folders")
        
        for date_folder in date_folders:
            date_str = date_folder.name
            session_id = self.generate_session_id(date_str)
            
            self.logger.info(f"\nProcessing date folder: {date_str}")
            self.logger.info(f"Session ID: {session_id}")
            
            # Check if session exists, create if needed
            if not self.verify_session_exists(session_id):
                if auto_create_sessions:
                    self.logger.warning(f"Session {session_id} not found, creating...")
                    if not self.create_missing_session(session_id, date_str):
                        self.logger.error(f"Failed to create session, skipping folder {date_str}")
                        continue
                else:
                    self.logger.error(f"Session {session_id} not found and auto_create_sessions=False, skipping")
                    continue
            
            # Get all observation folders
            obs_folders = sorted([f for f in date_folder.iterdir() 
                                 if f.is_dir() and re.match(r'^ch3_lib_\d{3}_\d{8}T\d{6}_\d{2}_l1$', f.name)])
            
            self.logger.info(f"  Found {len(obs_folders)} observation folders")
            
            for obs_folder in obs_folders:
                observation_code = obs_folder.name
                observation_id = self.generate_observation_id(observation_code)
                
                if not observation_id:
                    self.logger.warning(f"  Could not generate ID for {observation_code}")
                    self.stats['errors'] += 1
                    continue
                
                self.stats['total_found'] += 1
                
                # Find XML file
                xml_file = obs_folder / f"{observation_code}.xml"
                
                # Extract metadata
                if xml_file.exists():
                    metadata = self.parse_xml_metadata(xml_file)
                else:
                    self.logger.warning(f"  XML not found for {observation_code}, using defaults")
                    metadata = {
                        'start_time': None,
                        'stop_time': None,
                        'pds_version_id': '1.0',
                        'information_model_version': '1.11.0.0',
                        'processing_level': 'Calibrated',
                        'purpose': 'Science'
                    }
                
                # Create observation record
                observation = {
                    'observation_id': observation_id,
                    'session_id': session_id,
                    'logical_identifier': self.generate_logical_identifier(observation_code),
                    'observation_code': observation_code,
                    'observation_number': self.extract_sequence_number(observation_code),
                    'sub_index': self.extract_sub_index(observation_code) + 1,  # Add 1 to match your data
                    'start_time': metadata['start_time'],
                    'stop_time': metadata['stop_time'],
                    'pds_version_id': metadata['pds_version_id'],
                    'information_model_version': metadata['information_model_version'],
                    'processing_level': metadata['processing_level'],
                    'purpose': metadata['purpose']
                }
                
                # Insert into database
                self.insert_observation(observation)
        
        self.logger.info("\n" + "="*70)
        self.logger.info("INSERTION COMPLETE")
        self.logger.info("="*70)
        self.logger.info(f"Total observations found: {self.stats['total_found']}")
        self.logger.info(f"Successfully inserted: {self.stats['inserted']}")
        self.logger.info(f"Skipped (already exist): {self.stats['skipped']}")
        self.logger.info(f"Errors: {self.stats['errors']}")
        self.logger.info(f"Sessions created: {self.stats['sessions_created']}")
        self.logger.info("="*70)
        
        return self.stats['inserted']


def main():
    """Main function to run the database insertion."""
    
    print("="*70)
    print("OBSERVATION DATABASE INSERTION TOOL")
    print("PostgreSQL Version")
    print("="*70)
    print("\nThis script will:")
    print("1. Crawl the ch3_libs directory structure")
    print("2. Extract observation data from folders and XML files")
    print("3. Generate new observation IDs based on timestamps")
    print("4. Insert data directly into PostgreSQL database")
    print("="*70 + "\n")
    
    # Get directory path
    base_path = input("Enter the full path to the calibrated data directory\n(e.g., D:\\ch3_libs\\lib-v2\\data\\calibrated): ").strip()
    
    if not base_path:
        print("Error: No path provided")
        return
    
    # Get database configuration
    print("\n" + "="*70)
    print("DATABASE CONFIGURATION")
    print("="*70)
    
    db_config = {}
    db_config['host'] = input("Database Host (default: localhost): ").strip() or 'localhost'
    db_config['port'] = input("Database Port (default: 5432): ").strip() or '5432'
    db_config['database'] = input("Database Name (default: LunarAtlas): ").strip() or 'LunarAtlas'
    db_config['user'] = input("Database User: ").strip()
    
    # Get password securely
    import getpass
    db_config['password'] = getpass.getpass("Database Password: ")
    
    # Convert port to int
    try:
        db_config['port'] = int(db_config['port'])
    except ValueError:
        print("Invalid port number, using default 5432")
        db_config['port'] = 5432
    
    # Confirm configuration
    print("\n" + "="*70)
    print("CONFIGURATION SUMMARY")
    print("="*70)
    print(f"Directory: {base_path}")
    print(f"Database Host: {db_config['host']}:{db_config['port']}")
    print(f"Database Name: {db_config['database']}")
    print(f"Database User: {db_config['user']}")
    print("="*70)
    
    proceed = input("\nProceed with insertion? (yes/no): ").strip().lower()
    if proceed not in ['yes', 'y']:
        print("Cancelled by user.")
        return
    
    # Create inserter
    inserter = ObservationDatabaseInserter(base_path, db_config)
    
    try:
        # Connect to database
        if not inserter.connect_to_database():
            print("\n✗ Failed to connect to database. Check your credentials and try again.")
            return
        
        # Load existing sessions
        if not inserter.load_existing_sessions():
            print("\n✗ Failed to load existing sessions.")
            return
        
        # Ask about auto-creating sessions
        auto_create = input("\nAutomatically create missing sessions? (yes/no, default: yes): ").strip().lower()
        auto_create_sessions = auto_create in ['yes', 'y', '']
        
        # Crawl and insert
        print("\nStarting insertion process...\n")
        inserted_count = inserter.crawl_and_insert(auto_create_sessions=auto_create_sessions)
        
        print(f"\n{'='*70}")
        print(f"✓ Process complete!")
        print(f"{'='*70}")
        print(f"\nTotal inserted: {inserted_count} observations")
        print(f"Check 'observation_db_insert.log' for detailed logs")
        
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Disconnect from database
        inserter.disconnect_from_database()


if __name__ == "__main__":
    main()
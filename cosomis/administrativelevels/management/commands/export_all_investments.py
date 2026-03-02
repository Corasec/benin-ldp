# yourapp/management/commands/export_all_investments.py
import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db.models import F, Value, Q
from django.db.models.functions import Concat
from investments.models import Investment, Project
from administrativelevels.models import AdministrativeLevel, Sector, Category

class Command(BaseCommand):
    help = 'Exports all investments to a CSV file with all available fields'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='investments_export.csv',
            help='Output CSV file path (default: investments_export.csv)',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['csv', 'json'],
            default='csv',
            help='Output format (default: csv)',
        )
        parser.add_argument(
            '--include-relations',
            action='store_true',
            default=True,
            help='Include related field details (default: True)',
        )
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=1000,
            help='Number of records to process at once (default: 1000)',
        )

    def handle(self, *args, **options):
        output_file = options['output']
        output_format = options['format']
        include_relations = options['include_relations']
        chunk_size = options['chunk_size']
        
        # Get total count for progress tracking
        total_count = Investment.objects.count()
        
        if total_count == 0:
            self.stdout.write(self.style.WARNING('No investments found in the database'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Found {total_count} investments to export'))
        
        # Prepare queryset with selected related fields to optimize queries
        investments_qs = Investment.objects.all().select_related(
            'sector',
            'sector__category',
            'administrative_level',
            'funded_by',
            'funded_by__organization',
            'funded_by__sector',
            'funded_by__owner'
        ).prefetch_related(
            'investmentdocument_set',
            'investmentimage_set'
        ).order_by('id')
        
        fieldnames = self.get_fieldnames(include_relations)
        
        if output_format == 'csv':
            self.export_to_csv(investments_qs, fieldnames, output_file, total_count, chunk_size)
        else:
            self.export_to_json(investments_qs, fieldnames, output_file, total_count, chunk_size)
        
        self.create_field_descriptions_file(fieldnames, output_file)
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Export completed successfully!'
        ))
        self.stdout.write(f'📁 File saved to: {output_file}')
        
        # Also save a backup with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = os.path.splitext(output_file)[0]
        extension = os.path.splitext(output_file)[1]
        backup_file = f"{base_name}_{timestamp}{extension}"
        
        if output_format == 'csv':
            self.export_to_csv(investments_qs, fieldnames, backup_file, total_count, chunk_size)
        else:
            self.export_to_json(investments_qs, fieldnames, backup_file, total_count, chunk_size)
        
        self.stdout.write(self.style.SUCCESS(f'💾 Backup saved to: {backup_file}'))
    
    def get_fieldnames(self, include_relations=True):
        """Get all field names for the CSV header"""
        
        # Base Investment fields
        fieldnames = [
            # Identifiers
            'id',
            'no_sql_id',
            'imported_project_id',
            
            # Basic information
            'title',
            'description',
            'ranking',
            
            # Costs
            'estimated_cost',
            'real_cost',
            
            # Dates and duration
            'start_date',
            'duration',
            'delays_consumed',
            'created_at',
            'updated_at',
            
            # Progress rates
            'physical_execution_rate',
            'financial_implementation_rate',
            
            # Status fields
            'investment_status',
            'investment_status_display',
            'project_status',
            'project_status_display',
            
            # Location
            'latitude',
            'longitude',
            
            # Responsible structure
            'responsible_structure',
            
            # Minority group endorsements
            'endorsed_by_youth',
            'endorsed_by_women',
            'endorsed_by_agriculturist',
            'endorsed_by_pastoralist',
            
            # Climate contribution
            'climate_contribution',
            'climate_contribution_text',
        ]
        
        if include_relations:
            # Related fields - Administrative Level (full hierarchy)
            relation_fields = [
                # Administrative Level (current)
                'administrative_level_id',
                'administrative_level_name',
                'administrative_level_type',
                'administrative_level_type_display',
                
                # Administrative Level - Parent (Arrondissement/City)
                'parent_level_id',
                'parent_level_name',
                'parent_level_type',
                
                # Administrative Level - Grandparent (Commune)
                'grandparent_level_id',
                'grandparent_level_name',
                'grandparent_level_type',
                
                # Administrative Level - Great Grandparent (Departement)
                'great_grandparent_id',
                'great_grandparent_name',
                'great_grandparent_type',
                
                # Administrative Level - Country
                'country_level_id',
                'country_level_name',
                
                # Sector and Category
                'sector_id',
                'sector_name',
                'sector_description',
                'category_id',
                'category_name',
                'category_description',
                
                # Funded By (Project)
                'funded_by_id',
                'funded_by_name',
                'funded_by_description',
                'funded_by_total_amount',
                'funded_by_start_date',
                'funded_by_end_date',
                'funded_by_source_of_financing',
                'funded_by_collaborators',
                
                # Project Organization
                'funded_by_organization_id',
                'funded_by_organization_name',
                'funded_by_organization_acronym',
                'funded_by_organization_type',
                
                # Project Owner (User)
                'funded_by_owner_id',
                'funded_by_owner_username',
                'funded_by_owner_email',
                
                # Project Sector (Category)
                'funded_by_sector_id',
                'funded_by_sector_name',
            ]
            fieldnames.extend(relation_fields)
        
        # Optional: Add document/image counts
        fieldnames.extend([
            'documents_count',
            'images_count',
        ])
        
        return fieldnames
    
    def get_investment_data(self, investment, fieldnames, include_relations=True):
        """Extract all data from an investment instance"""
        
        # Helper to get display value for choice fields
        def get_choice_display(obj, field_name, choices):
            value = getattr(obj, field_name, None)
            if value:
                return dict(choices).get(value, value)
            return None
        
        # Base data
        data = {
            # Identifiers
            'id': investment.id,
            'no_sql_id': investment.no_sql_id,
            'imported_project_id': investment.imported_project_id,
            
            # Basic information
            'title': investment.title,
            'description': investment.description,
            'ranking': investment.ranking,
            
            # Costs
            'estimated_cost': investment.estimated_cost,
            'real_cost': investment.real_cost,
            
            # Dates and duration
            'start_date': investment.start_date.isoformat() if investment.start_date else None,
            'duration': investment.duration,
            'delays_consumed': investment.delays_consumed,
            'created_at': investment.created_at.isoformat() if hasattr(investment, 'created_at') else None,
            'updated_at': investment.updated_at.isoformat() if hasattr(investment, 'updated_at') else None,
            
            # Progress rates
            'physical_execution_rate': investment.physical_execution_rate,
            'financial_implementation_rate': investment.financial_implementation_rate,
            
            # Status fields
            'investment_status': investment.investment_status,
            'investment_status_display': get_choice_display(
                investment, 'investment_status', Investment.INVESTMENT_STATUS_CHOICES
            ),
            'project_status': investment.project_status,
            'project_status_display': get_choice_display(
                investment, 'project_status', Investment.PROJECT_STATUS_CHOICES
            ),
            
            # Location
            'latitude': investment.latitude,
            'longitude': investment.longitude,
            
            # Responsible structure
            'responsible_structure': investment.responsible_structure,
            
            # Minority group endorsements
            'endorsed_by_youth': investment.endorsed_by_youth,
            'endorsed_by_women': investment.endorsed_by_women,
            'endorsed_by_agriculturist': investment.endorsed_by_agriculturist,
            'endorsed_by_pastoralist': investment.endorsed_by_pastoralist,
            
            # Climate contribution
            'climate_contribution': investment.climate_contribution,
            'climate_contribution_text': investment.climate_contribution_text,
            
            # Document and image counts
            'documents_count': investment.investmentdocument_set.count() if hasattr(investment, 'investmentdocument_set') else 0,
            'images_count': investment.investmentimage_set.count() if hasattr(investment, 'investmentimage_set') else 0,
        }
        
        if include_relations:
            # Administrative Level data
            adm_level = investment.administrative_level
            if adm_level:
                data.update({
                    'administrative_level_id': adm_level.id,
                    'administrative_level_name': adm_level.name,
                    'administrative_level_type': adm_level.type,
                    'administrative_level_type_display': adm_level.get_type_display() if hasattr(adm_level, 'get_type_display') else adm_level.type,
                })
                
                # Get parent hierarchy
                parent = adm_level.parent
                if parent:
                    data.update({
                        'parent_level_id': parent.id,
                        'parent_level_name': parent.name,
                        'parent_level_type': parent.type,
                    })
                    
                    grandparent = parent.parent
                    if grandparent:
                        data.update({
                            'grandparent_level_id': grandparent.id,
                            'grandparent_level_name': grandparent.name,
                            'grandparent_level_type': grandparent.type,
                        })
                        
                        great_grandparent = grandparent.parent
                        if great_grandparent:
                            data.update({
                                'great_grandparent_id': great_grandparent.id,
                                'great_grandparent_name': great_grandparent.name,
                                'great_grandparent_type': great_grandparent.type,
                            })
                            
                            country = great_grandparent.parent
                            if country:
                                data.update({
                                    'country_level_id': country.id,
                                    'country_level_name': country.name,
                                })
            
            # Sector and Category data
            if investment.sector:
                data.update({
                    'sector_id': investment.sector.id,
                    'sector_name': investment.sector.name,
                    'sector_description': investment.sector.description,
                })
                
                if investment.sector.category:
                    data.update({
                        'category_id': investment.sector.category.id,
                        'category_name': investment.sector.category.name,
                        'category_description': investment.sector.category.description,
                    })
            
            # Funded By (Project) data
            if investment.funded_by:
                project = investment.funded_by
                data.update({
                    'funded_by_id': project.id,
                    'funded_by_name': project.name,
                    'funded_by_description': project.description,
                    'funded_by_total_amount': project.total_amount,
                    'funded_by_start_date': project.start_date.isoformat() if project.start_date else None,
                    'funded_by_end_date': project.end_date.isoformat() if project.end_date else None,
                    'funded_by_source_of_financing': project.source_of_financing,
                    'funded_by_collaborators': project.collaborators,
                })
                
                # Project Organization
                if project.organization:
                    data.update({
                        'funded_by_organization_id': project.organization.id,
                        'funded_by_organization_name': project.organization.name,
                        'funded_by_organization_acronym': project.organization.acronym,
                        'funded_by_organization_type': project.organization.type,
                    })
                
                # Project Owner
                if project.owner:
                    data.update({
                        'funded_by_owner_id': project.owner.id,
                        'funded_by_owner_username': project.owner.username,
                        'funded_by_owner_email': project.owner.email,
                    })
                
                # Project Sector
                if project.sector:
                    data.update({
                        'funded_by_sector_id': project.sector.id,
                        'funded_by_sector_name': project.sector.name,
                    })
        
        # Filter to only requested fields
        return {k: v for k, v in data.items() if k in fieldnames}
    
    def export_to_csv(self, queryset, fieldnames, filepath, total_count, chunk_size):
        """Export data to CSV file in chunks"""
        
        self.stdout.write(f'\n📊 Exporting to CSV: {filepath}')
        self.stdout.write(f'📋 Total fields: {len(fieldnames)}')
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, restval='', extrasaction='ignore')
            writer.writeheader()
            
            processed = 0
            for investment in queryset.iterator(chunk_size=chunk_size):
                data = self.get_investment_data(investment, fieldnames)
                writer.writerow(data)
                
                processed += 1
                if processed % 100 == 0:
                    self.stdout.write(f'  Progress: {processed}/{total_count} records processed', ending='\r')
            
            self.stdout.write(f'  Progress: {processed}/{total_count} records processed ✓')
    
    def export_to_json(self, queryset, fieldnames, filepath, total_count, chunk_size):
        """Export data to JSON file"""
        import json
        
        self.stdout.write(f'\n📊 Exporting to JSON: {filepath}')
        self.stdout.write(f'📋 Total fields: {len(fieldnames)}')
        
        all_data = []
        processed = 0
        
        for investment in queryset.iterator(chunk_size=chunk_size):
            data = self.get_investment_data(investment, fieldnames)
            all_data.append(data)
            
            processed += 1
            if processed % 100 == 0:
                self.stdout.write(f'  Progress: {processed}/{total_count} records processed', ending='\r')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'export_date': datetime.now().isoformat(),
                'total_count': len(all_data),
                'fields': fieldnames,
                'investments': all_data
            }, f, ensure_ascii=False, indent=2)
        
        self.stdout.write(f'  Progress: {processed}/{total_count} records processed ✓')
    
    def create_field_descriptions_file(self, fieldnames, output_file):
        """Create a companion file with field descriptions"""
        base_name = os.path.splitext(output_file)[0]
        desc_file = f"{base_name}_field_descriptions.txt"
        
        descriptions = {
            # Identifiers
            'id': 'Unique identifier for the investment',
            'no_sql_id': 'ID from external NoSQL database',
            'imported_project_id': 'Original project ID from import source',
            
            # Basic information
            'title': 'Title/name of the investment',
            'description': 'Detailed description of the investment',
            'ranking': 'Priority ranking number',
            
            # Costs
            'estimated_cost': 'Estimated cost in FCFA',
            'real_cost': 'Actual/realized cost in FCFA',
            
            # Dates and duration
            'start_date': 'Project start date',
            'duration': 'Planned duration in days',
            'delays_consumed': 'Number of delay days consumed',
            'created_at': 'Record creation timestamp',
            'updated_at': 'Record last update timestamp',
            
            # Progress rates
            'physical_execution_rate': 'Physical completion percentage',
            'financial_implementation_rate': 'Financial implementation percentage',
            
            # Status fields
            'investment_status': 'Investment type (p=priority, s=subproject)',
            'investment_status_display': 'Display name for investment status',
            'project_status': 'Project status (N=Not Funded, F=Funded, P=In Progress, C=Completed, PA=Paused)',
            'project_status_display': 'Display name for project status',
            
            # Location
            'latitude': 'Geographic latitude coordinate',
            'longitude': 'Geographic longitude coordinate',
            
            # Responsible structure
            'responsible_structure': 'Organization/entity responsible for implementation',
            
            # Minority group endorsements
            'endorsed_by_youth': 'Boolean: Endorsed by youth groups',
            'endorsed_by_women': 'Boolean: Endorsed by women groups',
            'endorsed_by_agriculturist': 'Boolean: Endorsed by farmer/agriculturist groups',
            'endorsed_by_pastoralist': 'Boolean: Endorsed by pastoralist groups',
            
            # Climate contribution
            'climate_contribution': 'Boolean: Has climate adaptation/mitigation contribution',
            'climate_contribution_text': 'Description of climate contribution',
            
            # Administrative Level fields
            'administrative_level_id': 'ID of the administrative level',
            'administrative_level_name': 'Name of the administrative level (village/city/commune)',
            'administrative_level_type': 'Type code of administrative level',
            'administrative_level_type_display': 'Display name of administrative level type',
            
            # Parent hierarchy fields
            'parent_level_id': 'ID of parent administrative level',
            'parent_level_name': 'Name of parent administrative level',
            'parent_level_type': 'Type of parent administrative level',
            'grandparent_level_id': 'ID of grandparent administrative level',
            'grandparent_level_name': 'Name of grandparent administrative level',
            'grandparent_level_type': 'Type of grandparent administrative level',
            'great_grandparent_id': 'ID of great-grandparent administrative level',
            'great_grandparent_name': 'Name of great-grandparent administrative level',
            'great_grandparent_type': 'Type of great-grandparent administrative level',
            'country_level_id': 'ID of country level',
            'country_level_name': 'Name of country',
            
            # Sector and Category fields
            'sector_id': 'ID of the sector',
            'sector_name': 'Name of the sector',
            'sector_description': 'Description of the sector',
            'category_id': 'ID of the category',
            'category_name': 'Name of the category',
            'category_description': 'Description of the category',
            
            # Funded By (Project) fields
            'funded_by_id': 'ID of the funding project',
            'funded_by_name': 'Name of the funding project',
            'funded_by_description': 'Description of the funding project',
            'funded_by_total_amount': 'Total amount of funding project',
            'funded_by_start_date': 'Start date of funding project',
            'funded_by_end_date': 'End date of funding project',
            'funded_by_source_of_financing': 'Source of financing for the project',
            'funded_by_collaborators': 'Collaborators on the project',
            
            # Organization fields
            'funded_by_organization_id': 'ID of implementing organization',
            'funded_by_organization_name': 'Name of implementing organization',
            'funded_by_organization_acronym': 'Acronym of implementing organization',
            'funded_by_organization_type': 'Type of organization',
            
            # Owner fields
            'funded_by_owner_id': 'ID of project owner/user',
            'funded_by_owner_username': 'Username of project owner',
            'funded_by_owner_email': 'Email of project owner',
            
            # Project Sector fields
            'funded_by_sector_id': 'ID of project sector',
            'funded_by_sector_name': 'Name of project sector',
            
            # Document counts
            'documents_count': 'Number of associated documents',
            'images_count': 'Number of associated images',
        }
        
        with open(desc_file, 'w', encoding='utf-8') as f:
            f.write("FIELD DESCRIPTIONS FOR INVESTMENTS EXPORT\n")
            f.write("="*80 + "\n\n")
            f.write(f"Export file: {os.path.basename(output_file)}\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total fields: {len(fieldnames)}\n\n")
            f.write("-"*80 + "\n\n")
            
            for field in fieldnames:
                description = descriptions.get(field, 'No description available')
                f.write(f"{field}:\n    {description}\n\n")
        
        self.stdout.write(self.style.SUCCESS(f'📝 Field descriptions saved to: {desc_file}'))
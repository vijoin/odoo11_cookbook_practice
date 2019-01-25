{
    'name': 'My Module Cookbook 11',
    'summary': 'Module for practicing Cookbook 11',
    'version': '11.0.1.0.0',
    'category': 'Uncategorized',
    'website': 'https://codex.com.ve/',
    'author': 'Alexandre Fayolle, Holger Brunn, Victor Inojosa',
    'application': False,
    'installable': True,
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    'depends': [
        'base',
                ],
    'data': [
        'views/library_book.xml',
        'security/groups.xml',
        'security/ir.model.access.csv'
    ],
}

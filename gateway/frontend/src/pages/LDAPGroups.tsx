import React, { useState, useEffect } from 'react';
import {
  Users,
  Shield,
  UserPlus,
  UserMinus,
  Search,
  RefreshCw,
  ChevronRight,
  Mail,
  AlertCircle,
  CheckCircle,
  Globe,
  Printer,
  Building2,
  Briefcase,
  DollarSign,
  Monitor,
  Megaphone,
  Key,
  FolderOpen
} from 'lucide-react';
import api from '../lib/api';

interface GroupInfo {
  cn: string;
  dn: string;
  description: string | null;
  member_count: number;
}

interface GroupMember {
  dn: string;
  uid: string;
  cn: string | null;
  mail: string | null;
}

interface GroupDetails {
  cn: string;
  dn: string;
  description: string | null;
  members: GroupMember[];
}

interface LDAPUser {
  uid: string;
  cn: string | null;
  mail: string | null;
}

// Icônes par groupe
const groupIcons: Record<string, React.ReactNode> = {
  'Employee': <Users className="w-5 h-5" />,
  'Internet': <Globe className="w-5 h-5" />,
  'Printer': <Printer className="w-5 h-5" />,
  'Public_Share_Folder_SharePoint': <FolderOpen className="w-5 h-5" />,
  'Finance': <DollarSign className="w-5 h-5" />,
  'IT': <Monitor className="w-5 h-5" />,
  'HR': <Users className="w-5 h-5" />,
  'Marketing': <Megaphone className="w-5 h-5" />,
  'Sales': <Briefcase className="w-5 h-5" />,
  'Management': <Building2 className="w-5 h-5" />,
  'VPN': <Key className="w-5 h-5" />,
  'Admin': <Shield className="w-5 h-5" />,
};

// Descriptions des groupes
const groupDescriptions: Record<string, string> = {
  'Employee': 'Accès de base pour tous les employés',
  'Internet': 'Accès à Internet',
  'Printer': 'Accès aux imprimantes',
  'Public_Share_Folder_SharePoint': 'Accès aux dossiers partagés SharePoint',
  'Finance': 'Département Finance',
  'IT': 'Département Informatique',
  'HR': 'Département Ressources Humaines',
  'Marketing': 'Département Marketing',
  'Sales': 'Département Ventes',
  'Management': 'Direction et Management',
  'VPN': 'Accès VPN distant',
  'Admin': 'Administrateurs système',
};

export default function LDAPGroups() {
  const [groups, setGroups] = useState<GroupInfo[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<GroupDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [addUsername, setAddUsername] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [userSuggestions, setUserSuggestions] = useState<LDAPUser[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  useEffect(() => {
    fetchGroups();
  }, []);

  // Recherche d'utilisateurs avec debounce
  useEffect(() => {
    if (addUsername.length < 1) {
      setUserSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const timer = setTimeout(() => {
      searchUsers(addUsername);
    }, 300);

    return () => clearTimeout(timer);
  }, [addUsername]);

  const searchUsers = async (query: string) => {
    setLoadingSuggestions(true);
    try {
      const response = await api.get(`/ldap/groups/users/search?q=${encodeURIComponent(query)}&limit=10`);
      setUserSuggestions(response.data);
      setShowSuggestions(true);
    } catch (error) {
      console.error('Error searching users:', error);
      setUserSuggestions([]);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const selectUser = (user: LDAPUser) => {
    setAddUsername(user.uid);
    setShowSuggestions(false);
    setUserSuggestions([]);
  };

  const fetchGroups = async () => {
    setLoading(true);
    try {
      const response = await api.get('/ldap/groups');
      setGroups(response.data);
    } catch (error) {
      console.error('Error fetching groups:', error);
      setMessage({ type: 'error', text: 'Erreur lors du chargement des groupes' });
    } finally {
      setLoading(false);
    }
  };

  const fetchGroupDetails = async (groupName: string) => {
    setLoadingDetails(true);
    try {
      const response = await api.get(`/ldap/groups/${groupName}`);
      setSelectedGroup(response.data);
    } catch (error) {
      console.error('Error fetching group details:', error);
      setMessage({ type: 'error', text: 'Erreur lors du chargement des détails du groupe' });
    } finally {
      setLoadingDetails(false);
    }
  };

  const addMember = async () => {
    if (!selectedGroup || !addUsername.trim()) return;

    setActionLoading(true);
    try {
      await api.post(`/ldap/groups/${selectedGroup.cn}/members`, {
        username: addUsername.trim()
      });
      setMessage({ type: 'success', text: `Utilisateur '${addUsername}' ajouté au groupe '${selectedGroup.cn}'` });
      setAddUsername('');
      // Rafraîchir les détails du groupe
      await fetchGroupDetails(selectedGroup.cn);
      // Rafraîchir la liste des groupes pour le compteur
      await fetchGroups();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Erreur lors de l\'ajout';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setActionLoading(false);
    }
  };

  const removeMember = async (username: string) => {
    if (!selectedGroup) return;

    if (!confirm(`Voulez-vous vraiment retirer '${username}' du groupe '${selectedGroup.cn}' ?`)) {
      return;
    }

    setActionLoading(true);
    try {
      await api.delete(`/ldap/groups/${selectedGroup.cn}/members/${username}`);
      setMessage({ type: 'success', text: `Utilisateur '${username}' retiré du groupe '${selectedGroup.cn}'` });
      // Rafraîchir les détails du groupe
      await fetchGroupDetails(selectedGroup.cn);
      // Rafraîchir la liste des groupes pour le compteur
      await fetchGroups();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Erreur lors du retrait';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setActionLoading(false);
    }
  };

  const filteredGroups = groups.filter(group =>
    group.cn.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Catégoriser les groupes
  const accessGroups = filteredGroups.filter(g =>
    ['Employee', 'Internet', 'Printer', 'Public_Share_Folder_SharePoint', 'VPN'].includes(g.cn)
  );
  const departmentGroups = filteredGroups.filter(g =>
    ['Finance', 'IT', 'HR', 'Marketing', 'Sales', 'Management'].includes(g.cn)
  );
  const adminGroups = filteredGroups.filter(g =>
    ['Admin'].includes(g.cn)
  );
  const otherGroups = filteredGroups.filter(g =>
    !accessGroups.includes(g) && !departmentGroups.includes(g) && !adminGroups.includes(g)
  );

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Shield className="w-8 h-8 text-blue-600" />
            Gestion des Groupes LDAP
          </h1>
          <p className="mt-2 text-gray-600">
            Gérez les groupes et leurs membres dans l'annuaire LDAP
          </p>
        </div>

        {/* Message */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg flex items-center gap-2 ${
            message.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {message.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
            {message.text}
            <button onClick={() => setMessage(null)} className="ml-auto text-lg">&times;</button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Liste des groupes */}
          <div className="lg:col-span-1 bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Groupes</h2>
                <button
                  onClick={fetchGroups}
                  className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                >
                  <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                </button>
              </div>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Rechercher un groupe..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="overflow-y-auto max-h-[calc(100vh-300px)]">
              {loading ? (
                <div className="p-8 text-center text-gray-500">
                  <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
                  Chargement...
                </div>
              ) : (
                <>
                  {/* Groupes d'accès */}
                  {accessGroups.length > 0 && (
                    <div className="p-3">
                      <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Accès</h3>
                      {accessGroups.map(group => (
                        <GroupItem
                          key={group.cn}
                          group={group}
                          isSelected={selectedGroup?.cn === group.cn}
                          onClick={() => fetchGroupDetails(group.cn)}
                        />
                      ))}
                    </div>
                  )}

                  {/* Départements */}
                  {departmentGroups.length > 0 && (
                    <div className="p-3 border-t border-gray-100">
                      <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Départements</h3>
                      {departmentGroups.map(group => (
                        <GroupItem
                          key={group.cn}
                          group={group}
                          isSelected={selectedGroup?.cn === group.cn}
                          onClick={() => fetchGroupDetails(group.cn)}
                        />
                      ))}
                    </div>
                  )}

                  {/* Admin */}
                  {adminGroups.length > 0 && (
                    <div className="p-3 border-t border-gray-100">
                      <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Administration</h3>
                      {adminGroups.map(group => (
                        <GroupItem
                          key={group.cn}
                          group={group}
                          isSelected={selectedGroup?.cn === group.cn}
                          onClick={() => fetchGroupDetails(group.cn)}
                        />
                      ))}
                    </div>
                  )}

                  {/* Autres */}
                  {otherGroups.length > 0 && (
                    <div className="p-3 border-t border-gray-100">
                      <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Autres</h3>
                      {otherGroups.map(group => (
                        <GroupItem
                          key={group.cn}
                          group={group}
                          isSelected={selectedGroup?.cn === group.cn}
                          onClick={() => fetchGroupDetails(group.cn)}
                        />
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Détails du groupe */}
          <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200">
            {loadingDetails ? (
              <div className="p-8 text-center text-gray-500">
                <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
                Chargement des détails...
              </div>
            ) : selectedGroup ? (
              <>
                {/* Header du groupe */}
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-blue-100 rounded-lg text-blue-600">
                        {groupIcons[selectedGroup.cn] || <Users className="w-6 h-6" />}
                      </div>
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900">{selectedGroup.cn}</h2>
                        <p className="text-gray-500">
                          {groupDescriptions[selectedGroup.cn] || selectedGroup.description || 'Groupe LDAP'}
                        </p>
                        <p className="text-sm text-gray-400 mt-1">{selectedGroup.dn}</p>
                      </div>
                    </div>
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                      {selectedGroup.members.length} membre{selectedGroup.members.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                </div>

                {/* Ajouter un membre */}
                <div className="p-4 border-b border-gray-200 bg-gray-50">
                  <div className="flex gap-2 relative">
                    <div className="flex-1 relative">
                      <input
                        type="text"
                        placeholder="Tapez pour rechercher un utilisateur..."
                        value={addUsername}
                        onChange={(e) => setAddUsername(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && addMember()}
                        onFocus={() => addUsername.length >= 1 && setShowSuggestions(true)}
                        onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                      {/* Liste des suggestions */}
                      {showSuggestions && userSuggestions.length > 0 && (
                        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                          {loadingSuggestions ? (
                            <div className="p-3 text-center text-gray-500">
                              <RefreshCw className="w-4 h-4 animate-spin inline mr-2" />
                              Recherche...
                            </div>
                          ) : (
                            userSuggestions.map((user) => (
                              <button
                                key={user.uid}
                                onClick={() => selectUser(user)}
                                className="w-full px-4 py-2 text-left hover:bg-blue-50 flex items-center gap-3 border-b border-gray-100 last:border-0"
                              >
                                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-medium text-sm">
                                  {user.uid.charAt(0).toUpperCase()}
                                </div>
                                <div className="flex-1">
                                  <div className="font-medium text-gray-900">{user.uid}</div>
                                  <div className="text-sm text-gray-500">
                                    {user.cn || ''} {user.mail && `• ${user.mail}`}
                                  </div>
                                </div>
                              </button>
                            ))
                          )}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={addMember}
                      disabled={!addUsername.trim() || actionLoading}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      <UserPlus className="w-4 h-4" />
                      Ajouter
                    </button>
                  </div>
                </div>

                {/* Liste des membres */}
                <div className="overflow-y-auto max-h-[calc(100vh-450px)]">
                  {selectedGroup.members.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">
                      <Users className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                      Aucun membre dans ce groupe
                    </div>
                  ) : (
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Utilisateur</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nom complet</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {selectedGroup.members.map((member) => (
                          <tr key={member.uid} className="hover:bg-gray-50">
                            <td className="px-6 py-4">
                              <span className="font-medium text-gray-900">{member.uid}</span>
                            </td>
                            <td className="px-6 py-4 text-gray-600">
                              {member.cn || '-'}
                            </td>
                            <td className="px-6 py-4">
                              {member.mail ? (
                                <a href={`mailto:${member.mail}`} className="text-blue-600 hover:underline flex items-center gap-1">
                                  <Mail className="w-4 h-4" />
                                  {member.mail}
                                </a>
                              ) : (
                                <span className="text-gray-400">-</span>
                              )}
                            </td>
                            <td className="px-6 py-4 text-right">
                              <button
                                onClick={() => removeMember(member.uid)}
                                disabled={actionLoading}
                                className="p-2 text-red-600 hover:bg-red-50 rounded-lg disabled:opacity-50"
                                title="Retirer du groupe"
                              >
                                <UserMinus className="w-4 h-4" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </>
            ) : (
              <div className="p-12 text-center text-gray-500">
                <Shield className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Sélectionnez un groupe</h3>
                <p>Cliquez sur un groupe à gauche pour voir ses membres et les gérer</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Composant pour un item de groupe
function GroupItem({ group, isSelected, onClick }: { group: GroupInfo; isSelected: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`w-full p-3 rounded-lg flex items-center gap-3 transition-colors ${
        isSelected
          ? 'bg-blue-100 text-blue-900'
          : 'hover:bg-gray-100 text-gray-700'
      }`}
    >
      <div className={`p-2 rounded-lg ${isSelected ? 'bg-blue-200' : 'bg-gray-100'}`}>
        {groupIcons[group.cn] || <Users className="w-4 h-4" />}
      </div>
      <div className="flex-1 text-left">
        <div className="font-medium">{group.cn}</div>
        <div className="text-xs text-gray-500">
          {group.member_count} membre{group.member_count !== 1 ? 's' : ''}
        </div>
      </div>
      <ChevronRight className={`w-4 h-4 ${isSelected ? 'text-blue-600' : 'text-gray-400'}`} />
    </button>
  );
}
